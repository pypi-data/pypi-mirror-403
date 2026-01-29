<!--
 Copyright (c) 2026 Anthony Mugendi
 
 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
-->

# Flexible Rate Limiter

A high-performance, Redis-backed rate limiter for **FastAPI** applications. 

Unlike standard rate limiters that apply static limits per endpoint, **Flexible Rate Limiter** allows you to enforce limits based on user-specific plans injected into the request state. It supports **atomic operations** via Lua scripts, ensuring data integrity even under high concurrency.

## Features

- ⚡ **High Performance**: Uses **Lua scripting** to perform check-and-decrement operations atomically in a single network round-trip.
- 🧠 **Context Aware**: Reads limits dynamically from `request.state`, enabling tiered limits (e.g., Free vs. Enterprise).
- 🛡️ **Fail-Open Design**: If Redis becomes unreachable, the limiter automatically allows requests to proceed, preventing your API from crashing (Reliability > Strictness).
- 🌍 **Scopes**: Support for both **Endpoint-specific** limits (Local) and **Global** API limits.
- ⚖️ **Weighted Costs**: Assign different costs to expensive endpoints statically or dynamically.
- ⏱️ **Flexible Windows**: Supports natural language durations (e.g., "1 hour", "2 days").
- 🗣️ **Humanized Errors**: Returns "Try again in 5 minutes" style messages.

## Installation

```bash
pip install flexible-rate-limiter
```

*Note: Requires a running Redis instance.*

## 🚀 Best Used With

While this package can function standalone, it is designed to work seamlessly with **[subs-webhook](https://github.com/mugendi/subs-webhook)**.

`subs-webhook` handles the complexity of API keys, plan management, and webhooks (e.g., Pabbly), automatically populating the `request.state.rate_limit` configuration that this package consumes.

### Integration Example

```python
from fastapi import FastAPI, Depends
from subs_webhook import init_subs, validate_access
from flexible_rate_limiter import RateLimiter

app = FastAPI()

# 1. Initialize Subscription System (Handles Auth, Plans & State Injection)
init_subs(app, sqlite_path="./subs.db", redis_url="redis://localhost:6379/0")

# 2. Initialize Rate Limiter
limiter = RateLimiter(redis_url="redis://localhost:6379/0")

# Load your plan permissions (JSON config)
plans_config = { 
    "cost": 1, 
    "limit": 2000,     
    "window": "1 day",  

    # Rate specific for route
    "/api/v1/rates/analytics": {  
        "cost": 5,      
        "limit": 200, 
        "window": "1 day"
    }
 } 

# 3. Protect Route
@app.get("/api/analytics", dependencies=[
    # validate_access checks permissions and injects request.state.rate_limit
    Depends(validate_access(plans_config)),
    # limiter reads that state and enforces the limit
    Depends(limiter)
])
async def get_analytics():
    return {"data": "..."}
```

## Prerequisites (Standalone Usage)

If you are **not** using `subs-webhook`, your authentication middleware must manually populate:

1. `request.state.api_key`: A unique identifier for the user.
2. `request.state.rate_limit`: A dictionary containing the rate limit configuration.

## Usage

### Basic Setup

Initialize the `RateLimiter` and add it as a dependency.

```python
from fastapi import FastAPI, Request, Depends
from flexible_rate_limiter import RateLimiter

app = FastAPI()

# Initialize the limiter (Default cost = 1)
limiter = RateLimiter(redis_url="redis://localhost:6379/0")

# Mock Middleware (Use this if NOT using subs-webhook)
@app.middleware("http")
async def attach_user_plan(request: Request, call_next):
    # In a real app, this is fetched from DB/Redis based on the API Key
    request.state.api_key = "user_123" 
    
    # Inject Rate Limit Configuration
    request.state.rate_limit = {
        "cost": 1,          
        "limit": 5000,      
        "window": "1 hour"  
    }
    
    response = await call_next(request)
    return response

# Apply to Routes
@app.get("/api/data", dependencies=[Depends(limiter)])
async def get_data():
    return {"message": "Request successful"}
```

## Configuration Structure

The `request.state.rate_limit` dictionary is flexible. It allows you to define a **Global Default** and specific **Route Overrides**.

### 1. Simple Global Limit
This applies the same limit (5000 requests per hour) to **every** endpoint the user accesses.

```json
{
    "cost": 1,
    "limit": 5000,
    "window": "1 hour"
}
```

### 2. Global Limit + Route Override
In this scenario, the user has a global bucket of 2000 requests per day. However, accessing the `/analytics` endpoint is restricted to a separate, smaller bucket (200 requests/day).

**Note:** Nested keys starting with `/` are treated as route-specific overrides (Local Scope).

```json
{
    "cost": 1,          // Default cost per request
    "limit": 2000,      // Global Limit
    "window": "1 day",  // Global Window

    "/api/v1/rates/analytics": {  // Route-Specific Override (Local Scope)
        "cost": 5,      // Expensive endpoint costs 5 units
        "limit": 200,   // Strict limit for this path
        "window": "1 day"
    }
}
```

### 3. Logic & Precedence
The `RateLimiter` determines which rule to apply based on the current request path:

1.  **Check for Override**: Does the config dictionary contain a key matching `request.url.path`?
    *   **Yes**: Use the settings inside that nested dictionary. The scope is **Local** (only hits to this specific path count against this limit).
2.  **Fallback to Default**: If no override exists, does the root dictionary contain `limit`?
    *   **Yes**: Use the root settings. The scope is **Global** (hits to any non-overridden path share this single counter).
3.  **No Config**: If neither exists, rate limiting is skipped.

## HTTP Responses

### Success (200 OK)
Headers indicate the limit that was applied (Global or Route-specific):

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 2000
X-RateLimit-Remaining: 1999
X-RateLimit-Window: 1 day
```

### Limit Exceeded (429 Too Many Requests)
```json
{
  "detail": "Rate limit exceeded. Try again in 15 minutes."
}
```

## Reliability

This package implements a **Fail-Open** strategy. If there is an error such as the Redis connection failing or timing out, the `RateLimiter` catches the error, logs it, and **allows the request to proceed**. This ensures your API service remains available even if the caching layer is down.

## Logging

To view error logs (e.g., Redis failures), configure the logger in your application startup:

```python
import logging

# Configure logging to see errors from the rate limiter
logging.basicConfig(level=logging.INFO)

# OR configure specifically for this library
logger = logging.getLogger("flexible_rate_limiter")
logger.setLevel(logging.ERROR)
```

## License

This software is released under the MIT License.
Copyright (c) 2026 Anthony Mugendi.
