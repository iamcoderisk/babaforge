from functools import wraps
from flask import request, jsonify, g
from datetime import datetime, timedelta
from app import db, redis_client
from app.models.api_key import APIRateLimit
import logging

logger = logging.getLogger(__name__)


def check_rate_limit(api_key_id, limits):
    """
    Check if request is within rate limits
    Returns (allowed: bool, remaining: dict, reset_time: dict)
    """
    now = datetime.utcnow()
    
    results = {
        'minute': {'allowed': True, 'remaining': limits['per_minute'], 'reset': None},
        'hour': {'allowed': True, 'remaining': limits['per_hour'], 'reset': None},
        'day': {'allowed': True, 'remaining': limits['per_day'], 'reset': None}
    }
    
    # Check each window
    windows = {
        'minute': (now.replace(second=0, microsecond=0), timedelta(minutes=1)),
        'hour': (now.replace(minute=0, second=0, microsecond=0), timedelta(hours=1)),
        'day': (now.replace(hour=0, minute=0, second=0, microsecond=0), timedelta(days=1))
    }
    
    for window_type, (window_start, window_duration) in windows.items():
        # Try Redis first (fast)
        try:
            redis_key = f"rate_limit:{api_key_id}:{window_type}:{window_start.isoformat()}"
            count = redis_client.get(redis_key)
            
            if count is None:
                # Not in Redis, check database
                rate_limit = APIRateLimit.query.filter_by(
                    api_key_id=api_key_id,
                    window_start=window_start,
                    window_type=window_type
                ).first()
                
                count = rate_limit.request_count if rate_limit else 0
                
                # Cache in Redis
                redis_client.setex(redis_key, int(window_duration.total_seconds()), count)
            else:
                count = int(count)
            
            # Check limit
            limit_key = f'per_{window_type}'
            max_requests = limits[limit_key]
            
            if count >= max_requests:
                results[window_type]['allowed'] = False
            
            results[window_type]['remaining'] = max(0, max_requests - count)
            results[window_type]['reset'] = (window_start + window_duration).isoformat()
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # On error, allow request (fail open)
            pass
    
    # Overall decision
    allowed = all(r['allowed'] for r in results.values())
    
    return allowed, results


def increment_rate_limit(api_key_id, limits):
    """Increment rate limit counters"""
    now = datetime.utcnow()
    
    windows = {
        'minute': (now.replace(second=0, microsecond=0), timedelta(minutes=1)),
        'hour': (now.replace(minute=0, second=0, microsecond=0), timedelta(hours=1)),
        'day': (now.replace(hour=0, minute=0, second=0, microsecond=0), timedelta(days=1))
    }
    
    for window_type, (window_start, window_duration) in windows.items():
        try:
            # Increment Redis
            redis_key = f"rate_limit:{api_key_id}:{window_type}:{window_start.isoformat()}"
            redis_client.incr(redis_key)
            redis_client.expire(redis_key, int(window_duration.total_seconds()))
            
            # Update database (async would be better)
            rate_limit = APIRateLimit.query.filter_by(
                api_key_id=api_key_id,
                window_start=window_start,
                window_type=window_type
            ).first()
            
            if rate_limit:
                rate_limit.request_count += 1
            else:
                rate_limit = APIRateLimit(
                    api_key_id=api_key_id,
                    window_start=window_start,
                    window_type=window_type,
                    request_count=1
                )
                db.session.add(rate_limit)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Rate limit increment error: {e}")
            db.session.rollback()


def rate_limit_decorator(f):
    """Decorator to enforce rate limits"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'api_key'):
            return f(*args, **kwargs)
        
        api_key = g.api_key
        limits = {
            'per_minute': api_key.rate_limit_per_minute,
            'per_hour': api_key.rate_limit_per_hour,
            'per_day': api_key.rate_limit_per_day
        }
        
        # Check rate limit
        allowed, results = check_rate_limit(api_key.id, limits)
        
        if not allowed:
            # Find which limit was exceeded
            exceeded = [k for k, v in results.items() if not v['allowed']][0]
            
            return jsonify({
                'error': 'rate_limit_exceeded',
                'message': f'Rate limit exceeded for {exceeded} window',
                'rate_limits': results
            }), 429
        
        # Increment counter
        increment_rate_limit(api_key.id, limits)
        
        # Add headers
        response = f(*args, **kwargs)
        
        if isinstance(response, tuple):
            response_obj, status_code = response[0], response[1] if len(response) > 1 else 200
        else:
            response_obj, status_code = response, 200
        
        # Add rate limit headers
        if hasattr(response_obj, 'headers'):
            response_obj.headers['X-RateLimit-Limit-Minute'] = str(limits['per_minute'])
            response_obj.headers['X-RateLimit-Remaining-Minute'] = str(results['minute']['remaining'])
            response_obj.headers['X-RateLimit-Reset-Minute'] = results['minute']['reset']
        
        return response_obj, status_code
    
    return decorated_function
