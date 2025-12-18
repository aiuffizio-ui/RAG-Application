import hashlib
import json
import logging
from typing import Optional, Dict, Any
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache for storing query-answer pairs."""
    
    _instance: Optional['RedisCache'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.client: Optional[redis.Redis] = None
        self.enabled = False
        self._connect()
    
    def _connect(self):
        """Connect to Redis server."""
        if not settings.REDIS_URL:
            logger.warning("REDIS_URL not set. Caching disabled.")
            return
            
        try:
            self.client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
            # Test connection
            self.client.ping()
            self.enabled = True
            logger.info(f"Connected to Redis at {settings.REDIS_URL}")
        except redis.ConnectionError as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
            self.enabled = False
    
    def _get_cache_key(self, query: str, top_k: int) -> str:
        """Generate cache key from query and parameters."""
        key_data = f"{query.lower().strip()}:{top_k}"
        return f"rag:query:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    def get(self, query: str, top_k: int = 8) -> Optional[Dict[str, Any]]:
        """Get cached response for a query."""
        if not self.enabled or not self.client:
            return None
            
        try:
            key = self._get_cache_key(query, top_k)
            cached = self.client.get(key)
            if cached:
                logger.info(f"Cache hit for query: {query[:50]}...")
                return json.loads(cached)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, query: str, top_k: int, answer: str, sources: list) -> bool:
        """Cache a query response."""
        if not self.enabled or not self.client:
            return False
            
        try:
            key = self._get_cache_key(query, top_k)
            data = {
                "answer": answer,
                "sources": sources,
                "cached": True
            }
            self.client.setex(
                key,
                settings.CACHE_TTL,
                json.dumps(data)
            )
            logger.info(f"Cached response for query: {query[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def clear(self) -> int:
        """Clear all RAG query cache entries."""
        if not self.enabled or not self.client:
            return 0
            
        try:
            keys = self.client.keys("rag:query:*")
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0


def get_cache() -> RedisCache:
    """Get or create the Redis cache instance."""
    return RedisCache()
