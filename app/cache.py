import redis
import logging
from app import config

# Setup logger
logger = logging.getLogger("cache")
logger.setLevel(logging.INFO)

r = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=config.REDIS_DB,
    decode_responses=True,
    socket_connect_timeout=3600
)

def get_cache(key):
    try:
        value = r.get(key)
        if value:
            logger.info(f"[CACHE] Hit for key={key}")
        else:
            logger.info(f"[CACHE] Miss for key={key}")
        return value
    except redis.RedisError as e:
        logger.warning(f"[CACHE] Redis unavailable: {e}")
        return None

def set_cache(key, value, ttl=config.CACHE_TTL):
    try:
        r.setex(key, ttl, value)
        logger.info(f"[CACHE] Stored key={key} with TTL={ttl}s")
    except redis.RedisError as e:
        logger.warning(f"[CACHE] Could not store key={key}: {e}")
        
def clear_cache():
    """Clear all keys in Redis cache."""
    r.flushdb()
    logger.info("✅ Redis cache cleared")
