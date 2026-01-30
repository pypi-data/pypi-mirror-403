import time
from typing import Any, Optional


class CacheEntry:
    """Entrada individual do cache com timestamp."""
    
    __slots__ = ('value', 'timestamp')
    
    def __init__(self, value: Any):
        self.value = value
        self.timestamp = time.time()
    
    def is_expired(self, ttl: Optional[float]) -> bool:
        """Verifica se a entrada expirou."""
        return ttl is not None and (time.time() - self.timestamp) > ttl