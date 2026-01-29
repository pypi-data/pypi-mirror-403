"""
Copyright (c) 2026 Anthony Mugendi

This software is released under the MIT License.
https://opensource.org/licenses/MIT
"""

import humanize
import logging
from datetime import timedelta
from pytimeparse import parse
from fastapi import HTTPException, Request, Response
from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

# Lua script to handle check-and-decrement atomically
# Returns: [is_allowed (1/0), ttl_remaining, current_balance]
RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local cost = tonumber(ARGV[3])

local current = redis.call("GET", key)

-- If key doesn't exist, initialize it
if not current then
    redis.call("SET", key, limit, "EX", window)
    current = limit
end

local balance = tonumber(current)

-- Check if we have enough units
 if balance < cost then
    return {0, redis.call("TTL", key), 0} 
 end

-- Decrement and return new balance
local new_balance = redis.call("DECRBY", key, cost)
return {1, 0, new_balance}
"""


def seconds_to_duration(seconds: int) -> str:
    return humanize.naturaldelta(timedelta(seconds=seconds))


class RateLimiter:
    def __init__(self, redis_url: str, cost=1, window="1 day"):
        # Use a connection pool (redis-py does this by default with from_url)
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        # Pre-load script
        self.script = self.redis.register_script(RATE_LIMIT_SCRIPT)
        self.default_cost = cost
        self.default_window = window

    async def __call__(self, request: Request, response: Response):
        current_path = request.url.path
        # print(f"\n\n Called: {current_path}")
        try:
            # 1. Extract Config
            api_key = getattr(request.state, "api_key", None)

            if not api_key:
                # Fail safe: If no user, maybe allow or raise 500 depending on policy
                return

            rate_limit_config = getattr(request.state, "rate_limit", {})
            scope = "global"

            # if no rate limiting
            if rate_limit_config is None:
                return

            if current_path in rate_limit_config:
                scope = "local"
                # Route-specific override
                config = rate_limit_config[current_path]
            elif all(k in rate_limit_config for k in ["limit"]):
                # Default plan limits
                config = {
                    "cost": rate_limit_config.get("cost", self.default_cost),
                    "limit": rate_limit_config.get("limit"),
                    "window": rate_limit_config.get("window", self.default_window),
                }
            else:
                return

            limit = int(config["limit"])

            # set limit values and defaults
            cost = int(config.get("cost", self.default_cost))
            window_raw = config.get("window", self.default_window)

            # Parse window once
            seconds = (
                window_raw if isinstance(window_raw, int) else parse(str(window_raw))
            )
            if not seconds:
                seconds = 86400  # Default fallback

            print(
                f"{current_path} >> cost:{cost}, limit:{limit}, seconds:{seconds}, scope:{scope}"
            )

            if scope == "local":
                redis_key = f"user:fr-limit:{request.url.path}:{api_key}"
            else:
                redis_key = f"user:fr-limit:global:{api_key}"

            # 2. Execute Atomic Script
            # result[0] = is_allowed (1 or 0)
            # result[1] = ttl
            # result[2] = remaining_balance
            result = await self.script(keys=[redis_key], args=[limit, seconds, cost])

            is_allowed, ttl, remaining = result[0], result[1], result[2]

            # 3. Set Headers
            response.headers["X-RateLimit-Window"] = str(window_raw)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)

            # print(result, bool(is_allowed))

            # 4. Handle Block
            if not bool(is_allowed):
                response.headers["Retry-After"] = str(ttl)
                raise HTTPException(
                    headers=response.headers,
                    status_code=429,
                    detail=f"Rate limit exceeded. Try again in {seconds_to_duration(ttl)}.",
                )

        # raise http 429 errors 
        except HTTPException as e:
            raise e

        # log redis error
        except RedisError:
            # "Fail Open" strategy: If Redis is down, allow the request
            # so the API doesn't crash completely.
            logger.error(
                f"Rate Limiter Redis connection failed. Failing open. Error: {e}",
                exc_info=True,
            )

            # continue
            pass

        # log all other errors
        except Exception as e:
            print(f"ERROR {e}")
            print(e)
            logger.error(
                f"Rate Limiter failed. Failing open. Error: {e}",
                exc_info=True,
            )

            # continue
            pass
