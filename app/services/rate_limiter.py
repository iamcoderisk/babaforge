import asyncio
from typing import Dict, Optional
from datetime import datetime, timedelta
import redis.asyncio as redis

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class RateLimiter:
    """Token bucket rate limiter for email sending"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        
        # Domain-specific rate limits (emails per hour)
        self.domain_limits = {
            'gmail.com': settings.GMAIL_RATE_LIMIT,
            'googlemail.com': settings.GMAIL_RATE_LIMIT,
            'yahoo.com': settings.YAHOO_RATE_LIMIT,
            'outlook.com': settings.OUTLOOK_RATE_LIMIT,
            'hotmail.com': settings.OUTLOOK_RATE_LIMIT,
            'live.com': settings.OUTLOOK_RATE_LIMIT,
        }
        
        self.default_limit = settings.DEFAULT_RATE_LIMIT
    
    async def get_redis(self) -> redis.Redis:
        """Get Redis connection"""
        if not self.redis_client:
            self.redis_client = await redis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
                decode_responses=True
            )
        return self.redis_client
    
    async def check_rate(self, domain: str, ip: Optional[str] = None) -> bool:
        """
        Check if sending to domain is allowed (token bucket algorithm)
        Returns True if allowed, False if rate limited
        """
        r = await self.get_redis()
        
        # Get rate limit for domain
        limit = self.domain_limits.get(domain, self.default_limit)
        
        # Token bucket key
        key = f"ratelimit:domain:{domain}"
        if ip:
            key = f"ratelimit:domain:{domain}:ip:{ip}"
        
        # Implement token bucket
        now = datetime.now().timestamp()
        
        # Use Lua script for atomic operations
        lua_script = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local now = tonumber(ARGV[2])
        local window = tonumber(ARGV[3])
        local cost = tonumber(ARGV[4])
        
        local tokens_key = key .. ':tokens'
        local timestamp_key = key .. ':timestamp'
        
        local last_tokens = tonumber(redis.call('get', tokens_key)) or limit
        local last_timestamp = tonumber(redis.call('get', timestamp_key)) or now
        
        -- Calculate token regeneration
        local elapsed = now - last_timestamp
        local regenerated = (elapsed / window) * limit
        local new_tokens = math.min(limit, last_tokens + regenerated)
        
        -- Check if we have enough tokens
        if new_tokens >= cost then
            new_tokens = new_tokens - cost
            redis.call('set', tokens_key, new_tokens)
            redis.call('set', timestamp_key, now)
            redis.call('expire', tokens_key, window * 2)
            redis.call('expire', timestamp_key, window * 2)
            return 1
        else
            return 0
        end
        """
        
        try:
            # Execute Lua script
            result = await r.eval(
                lua_script,
                1,  # Number of keys
                key,  # KEYS[1]
                limit,  # ARGV[1] - rate limit
                now,  # ARGV[2] - current timestamp
                3600,  # ARGV[3] - window (1 hour in seconds)
                1  # ARGV[4] - cost (1 email)
            )
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Rate limiter error for {domain}: {e}")
            # Fail open - allow send on error
            return True
    
    async def get_current_rate(self, domain: str, ip: Optional[str] = None) -> Dict:
        """Get current rate limit status for domain"""
        r = await self.get_redis()
        
        key = f"ratelimit:domain:{domain}"
        if ip:
            key = f"ratelimit:domain:{domain}:ip:{ip}"
        
        tokens_key = f"{key}:tokens"
        timestamp_key = f"{key}:timestamp"
        
        limit = self.domain_limits.get(domain, self.default_limit)
        
        try:
            tokens = await r.get(tokens_key)
            timestamp = await r.get(timestamp_key)
            
            return {
                'domain': domain,
                'limit': limit,
                'available': float(tokens) if tokens else limit,
                'last_update': float(timestamp) if timestamp else None
            }
        except Exception as e:
            logger.error(f"Error getting rate status: {e}")
            return {'domain': domain, 'limit': limit, 'available': limit}
    
    async def update_domain_limit(self, domain: str, new_limit: int):
        """Update rate limit for a specific domain"""
        self.domain_limits[domain] = new_limit
        logger.info(f"Updated rate limit for {domain}: {new_limit}/hour")
    
    async def reset_rate_limit(self, domain: str, ip: Optional[str] = None):
        """Reset rate limit for domain"""
        r = await self.get_redis()
        
        key = f"ratelimit:domain:{domain}"
        if ip:
            key = f"ratelimit:domain:{domain}:ip:{ip}"
        
        await r.delete(f"{key}:tokens", f"{key}:timestamp")
        logger.info(f"Reset rate limit for {key}")
    
    async def get_all_rates(self) -> Dict:
        """Get rate status for all domains"""
        r = await self.get_redis()
        
        all_rates = {}
        pattern = "ratelimit:domain:*:tokens"
        
        async for key in r.scan_iter(match=pattern):
            domain = key.replace("ratelimit:domain:", "").replace(":tokens", "")
            rate_info = await self.get_current_rate(domain)
            all_rates[domain] = rate_info
        
        return all_rates
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()