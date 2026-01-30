from functools import wraps
from typing import Callable

from .lru_cache import LRUCache
from .cache_key_builder import CacheKeyBuilder
from .cache_stats import CacheStats
from .cache_backend import MISSING


def create_wrapper(
    func       : Callable,
    cache      : LRUCache,
    stats      : CacheStats,
    key_builder: CacheKeyBuilder,
    is_async   : bool
) -> Callable:
    """Cria wrapper apropriado (sync ou async)."""
    
    if is_async:
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            key = key_builder.build(self, args, kwargs)
            cached_value = cache.get(key)
            if cached_value is not MISSING:
                stats.record_hit()
                return cached_value
            
            stats.record_miss()
            result = await func(self, *args, **kwargs)
            cache.put(key, result)
            
            return result
        
        return async_wrapper
    
    else:
        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            key = key_builder.build(self, args, kwargs)
            cached_value = cache.get(key)
            if cached_value is not MISSING:
                stats.record_hit()
                return cached_value
            
            stats.record_miss()
            result = func(self, *args, **kwargs)
            cache.put(key, result)
            
            return result
        
        return sync_wrapper