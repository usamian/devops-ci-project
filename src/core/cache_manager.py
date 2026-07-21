"""
Atlas AI — Cache Manager
High-performance caching layer for models, queries, and computations.
Implements LRU cache with TTL for optimal performance.
"""

from __future__ import annotations
import time
import hashlib
import json
from typing import Any, Optional
from dataclasses import dataclass, field
from threading import Lock
from collections import OrderedDict


@dataclass
class CacheEntry:
    """A single cache entry with TTL support."""
    value: Any
    created_at: float
    ttl_seconds: int
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl_seconds
    
    def remaining_ttl(self) -> float:
        elapsed = time.time() - self.created_at
        return max(0, self.ttl_seconds - elapsed)


class LRUCache:
    """Thread-safe LRU cache with TTL support."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired():
                    # Move to end (most recently used)
                    self._cache.move_to_end(key)
                    self._hits += 1
                    return entry.value
                else:
                    # Remove expired entry
                    del self._cache[key]
                    self._evictions += 1
            
            self._misses += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        with self._lock:
            # Calculate size for complex objects
            try:
                size = len(json.dumps(value).encode('utf-8'))
            except:
                size = 100  # Default size for non-serializable objects
            
            entry = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl_seconds=ttl or self.default_ttl,
                size_bytes=size
            )
            
            # Remove oldest entries if at capacity
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
                self._evictions += 1
            
            self._cache[key] = entry
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
                self._evictions += 1
            return len(expired_keys)
    
    def stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2),
            "evictions": self._evictions,
        }


class ModelCache:
    """Singleton cache for ML models to avoid repeated loading."""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._models = {}
                    cls._instance._loaded_at = {}
        return cls._instance
    
    def get_model(self, model_name: str) -> Optional[Any]:
        """Get a loaded model instance."""
        return self._models.get(model_name)
    
    def set_model(self, model_name: str, model: Any) -> None:
        """Store a loaded model instance."""
        self._models[model_name] = model
        self._loaded_at[model_name] = time.time()
    
    def is_loaded(self, model_name: str) -> bool:
        """Check if a model is loaded."""
        return model_name in self._models
    
    def get_all_models(self) -> dict:
        """Get all loaded models."""
        return self._models.copy()
    
    def clear(self) -> None:
        """Clear all loaded models."""
        self._models.clear()
        self._loaded_at.clear()


# Global cache instances
_query_cache = None
_model_cache = None


def get_query_cache() -> LRUCache:
    """Get or create the global query cache."""
    global _query_cache
    if _query_cache is None:
        _query_cache = LRUCache(max_size=5000, default_ttl=3600)
    return _query_cache


def get_model_cache() -> ModelCache:
    """Get or create the global model cache."""
    global _model_cache
    if _model_cache is None:
        _model_cache = ModelCache()
    return _model_cache


def generate_cache_key(*args, **kwargs) -> str:
    """Generate a consistent cache key from arguments."""
    key_data = {
        "args": args,
        "kwargs": kwargs
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode('utf-8')).hexdigest()


def cleanup_all_caches() -> dict:
    """Run cleanup on all caches."""
    query_cache = get_query_cache()
    expired_count = query_cache.cleanup_expired()
    return {
        "query_cache_stats": query_cache.stats(),
        "expired_entries_removed": expired_count,
    }