from threading import RLock
from typing import Tuple


class CacheStats:
    """Estatísticas de uso do cache thread-safe."""
    
    __slots__ = ('hits', 'misses', '_lock')
    
    def __init__(self):
        self.hits   = 0
        self.misses = 0
        self._lock  = RLock()
    
    def record_hit(self):
        with self._lock:
             self.hits += 1
    
    def record_miss(self):
        with self._lock:
             self.misses += 1
    
    def get_stats(self) -> Tuple[int, int]:
        with self._lock:
            return (self.hits, self.misses)
    
    def hit_rate(self) -> float:
        with self._lock:
            total = self.hits + self.misses
            return round(self.hits / total, 4) if total > 0 else 0.0

