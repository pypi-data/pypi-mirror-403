from pydantic import BaseModel, RootModel, Field, field_validator
from typing import Dict, Any, List, Optional, Union


class RateLimitConfig(BaseModel):
    """
    Rate limit configuration for API requests.
    
    Fields:
        cost: The number of rate limit units consumed per request (default: 1)
        limit: Maximum number of requests allowed within the time window
        window: Time window for the rate limit (e.g., "1 day", "1 hour", "30 minutes")
    
    Examples:
        {"cost": 1, "limit": 100, "window": "1 hour"}
        {"cost": 5, "limit": 1000, "window": "1 day"}
    """
    cost: Optional[int] = Field(default=1, ge=1, description="Cost per request in rate limit units")
    limit: int = Field(..., ge=1, description="Maximum requests allowed in the time window")
    window: Optional[str] = Field(..., description="Time window (e.g., '1 day', '1 hour', '30 minutes')")


class Plan(BaseModel):
    """
    Plan configuration defining rate limits.
    
    Fields:
        rate_limit: Optional rate limiting configuration. Can include:
            - Default rate limit (applies to all routes)
            - Route-specific overrides (keyed by route path)
    
    Rate Limit Behavior:
        - If rate_limit is not present, no rate limiting is enforced
        - If rate_limit contains only cost/limit/window, those limits apply to ALL routes
        - If rate_limit contains route-specific keys (e.g., "/api/v1/rates/analytics"),
          those override the default limits for that specific route
        - Route-specific limits take precedence over default limits
    
    Example:
        {
            "rate_limit": {
                "cost": 1,
                "limit": 1000,
                "window": "1 day",
                "/api/v1/rates/analytics": {
                    "cost": 2,
                    "limit": 100,
                    "window": "1 hour"
                }
            }
        }
        
        In this example:
        - /api/v1/rates/history uses the default: 1000 requests per day, cost=1
        - /api/v1/rates/analytics uses the override: 100 requests per hour, cost=2
    """
    rate_limit: Optional[Dict[str, Any]] = Field(default=None)
    
    @field_validator('routes')
    @classmethod
    def validate_routes(cls, v):
        for route in v:
            if not isinstance(route, str) or not route.startswith('/'):
                raise ValueError(f"Route must be a path starting with '/': {route}")
        return v
    
    @field_validator('rate_limit')
    @classmethod
    def validate_rate_limit(cls, v):
        """
        Validate rate_limit structure.
        
        The rate_limit dict can contain:
        1. Default config with keys: cost, limit, window
        2. Route-specific configs keyed by route path
        3. A mix of both (default + route-specific overrides)
        """
        if v is None:
            return v
        
        # Check if there's a default rate limit (cost, limit, window at root level)
        has_default = all(key in v for key in ['cost', 'limit', 'window'])
        
        # Validate default config if present
        if has_default:
            try:
                RateLimitConfig(**{k: v[k] for k in ['cost', 'limit', 'window']})
            except Exception as e:
                raise ValueError(f"Invalid default rate limit config: {e}")
        
        # Validate route-specific configs
        for key, value in v.items():
            # Skip the default config keys
            if key in ['cost', 'limit', 'window']:
                continue
            
            # Route-specific configs must start with '/'
            if not key.startswith('/'):
                raise ValueError(f"Rate limit key must be a route path starting with '/': {key}")
            
            # Validate the route-specific config
            if not isinstance(value, dict):
                raise ValueError(f"Rate limit config for route '{key}' must be a dict")
            
            try:
                RateLimitConfig(**value)
            except Exception as e:
                raise ValueError(f"Invalid rate limit config for route '{key}': {e}")
        
        return v
    
    def get_rate_limit_for_route(self, route_path: str) -> Optional[RateLimitConfig]:
        """
        Get the applicable rate limit configuration for a specific route.
        
        Args:
            route_path: The API route path (e.g., "/api/v1/rates/analytics")
        
        Returns:
            RateLimitConfig if rate limiting is configured, None otherwise
        
        Priority:
            1. Route-specific override (if present)
            2. Default plan rate limit (if present)
            3. None (no rate limiting)
        """
        if self.rate_limit is None:
            return None
        
        # Check for route-specific override first
        if route_path in self.rate_limit:
            return RateLimitConfig(**self.rate_limit[route_path])
        
        # Fall back to default if it exists
        if all(key in self.rate_limit for key in ['cost', 'limit', 'window']):
            return RateLimitConfig(**{
                k: self.rate_limit[k] 
                for k in ['cost', 'limit', 'window']
            })
        
        return None


class PlansConfig(RootModel):
    """
    Root configuration for all plan types.
    
    Example:
        {
            "observer": { ... },
            "pro": { ... },
            "enterprise": { ... }
        }
    """
    root: Dict[str, Plan]
    
    def __getitem__(self, item):
        return self.root[item]
    
    def __iter__(self):
        return iter(self.root)
    
    def items(self):
        return self.root.items()