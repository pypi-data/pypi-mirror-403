import hashlib
from collections import OrderedDict
from threading import RLock
from typing import Any, Optional, Tuple

from .cache_backend import CacheBackend, MISSING
from .cache_entry import CacheEntry


class LRUCache:
    """Cache LRU thread-safe com suporte a TTL e persistência."""
    
    def __init__(
        self,
        capacity: int,
        ttl: Optional[float] = None,
        backend: Optional[CacheBackend] = None
    ):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        
        self.cache    = OrderedDict()
        self.capacity = capacity
        self.ttl      = ttl
        self.backend  = backend
        self._lock    = RLock()

    def get(self, key: Tuple) -> Optional[Any]:
        """Obtém valor do cache (memória + backend)."""
        with self._lock:
            # Try memory first
            value = self._get_from_memory(key)
            if value is not MISSING:
                return value
            
            # Fallback to backend
            return self._get_from_backend(key)
    
    def _get_from_memory(self, key: Tuple) -> Optional[Any]:
        """Tenta recuperar da memória."""
        if key not in self.cache:
            return MISSING
        
        entry = self.cache[key]
        
        if entry.is_expired(self.ttl):
            del self.cache[key]
            return MISSING
        
        self.cache.move_to_end(key)
        return entry.value
    
    def _get_from_backend(self, key: Tuple) -> Optional[Any]:
        """Tenta recuperar do backend."""
        if not self.backend:
            return MISSING
        
        try:
            key_str = self._serialize_key(key)
            value   = self.backend.get(key_str)
            
            if value is not MISSING:
                # Reconstruct in memory
                self.cache[key] = CacheEntry(value)
                self.cache.move_to_end(key)
                return value
        except Exception:
            pass  # Backend failures shouldn't crash
        
        return MISSING

    def put(self, key: Tuple, value: Any) -> None:
        """Adiciona valor no cache (memória + backend)."""
        with self._lock:
             self._put_in_memory(key, value)
             self._put_in_backend(key, value)
    
    def _put_in_memory(self, key: Tuple, value: Any) -> None:
        """Armazena na memória."""
        self.cache[key] = CacheEntry(value)
        self.cache.move_to_end(key)
        
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
    
    def _put_in_backend(self, key: Tuple, value: Any) -> None:
        """Armazena no backend."""
        if not self.backend:
            return
        
        try:
            key_str = self._serialize_key(key)
            self.backend.set(key_str, value, ttl=self.ttl)
        except Exception:
            pass  # Backend failures shouldn't crash
    
    def clear(self) -> None:
        """Limpa cache de memória."""
        with self._lock:
             self.cache.clear()
    
    def size(self) -> int:
        """Retorna tamanho atual do cache em memória."""
        with self._lock:
            return len(self.cache)
    
    @staticmethod
    def _serialize_key(key: Tuple) -> str:
        """Serializa chave tupla para string."""
        return hashlib.md5(str(key).encode()).hexdigest()
