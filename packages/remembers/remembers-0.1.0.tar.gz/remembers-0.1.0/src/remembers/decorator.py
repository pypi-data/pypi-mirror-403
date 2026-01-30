import asyncio
from typing import Any, Callable, Optional, List, TypeVar

from .func_wrapper import create_wrapper
from .cache_backend import CacheBackend
from .filesystem_backend import FileSystemBackend
from .lru_cache import LRUCache
from .cache_key_builder import CacheKeyBuilder
from .cache_stats import CacheStats


F = TypeVar('F', bound=Callable[..., Any])

def remember(
    maxsize: int = 128,
    typed: bool = False,
    key_args: Optional[List[str]] = None,
    ttl_seconds: Optional[float] = 300,
    persist: bool = False,
    backend: Optional[CacheBackend] = None,
    cache_dir: str = ".cache",
    file_ttl_days: int = 1,
    per_instance: bool = False
) -> Callable[[F], F]:
    """
    Decorador de cache LRU thread-safe com persistência opcional e compatível com async.
    
    Args:
        maxsize       : Número máximo de itens no cache em memória
        typed         : Se True, tipos diferentes são cacheados separadamente
        key_args      : Lista de argumentos/paths para chave (None = todos)
        ttl_seconds   : TTL para entradas em memória (None = sem expiração)
        persist       : Se True, habilita persistência em disco
        backend       : Backend customizado (None = usa FileSystemBackend)
        cache_dir     : Diretório para cache (usado se persist=True e backend=None)
        file_ttl_days : Dias até arquivos expirarem (padrão: 1)
        per_instance  : Se True, cache separado por instância (usa id()).
                        Se False e persist=True, cache compartilhado entre execuções
    
    Returns:
        Função decorada com cache (compatível com sync e async)
    """
    if maxsize <= 0:
        raise ValueError("maxsize must be positive")
    if ttl_seconds is not None and ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be positive or None")
    if file_ttl_days <= 0:
        raise ValueError("file_ttl_days must be positive")
    
    def decorator(func: F) -> F:
        # Setup backend
        cache_backend = None
        is_persistent = persist or (backend is not None)
        # persist=True ativa o file backend por padrão
        # porém se um backend customizado for fornecido,
        # fica implicito que o usuário quer usá-lo
        if is_persistent:
            cache_backend = backend or FileSystemBackend(
                cache_dir     = cache_dir,
                file_ttl_days = file_ttl_days,
                auto_cleanup  = True
            )
        
        # Initialize components
        cache = LRUCache(maxsize, ttl=ttl_seconds, backend=cache_backend)
        stats = CacheStats()
        
        use_stable_key = is_persistent and not per_instance
        key_builder = CacheKeyBuilder(func, key_args, typed, use_class_name=use_stable_key)
        
        # Detect if function is async
        is_async = asyncio.iscoroutinefunction(func)
        
        # Create appropriate wrapper
        wrapper = create_wrapper(func, cache, stats, key_builder, is_async)

        
        def cache_info():
            """Retorna informações sobre o cache."""
            hits, misses = stats.get_stats()
            info = {
                'hits'         : hits,
                'misses'       : misses,
                'currsize'     : cache.size(),
                'hit_rate'     : stats.hit_rate(),
                'is_async'     : is_async,
                'maxsize'      : maxsize,
                'per_instance' : per_instance,
                'persistent'   : persist or (cache_backend is not None),
            }
            
            if cache_backend and hasattr(cache_backend, 'get_stats'):
                info['backend_stats'] = cache_backend.get_stats() # type: ignore
            
            return info
        
        wrapper.cache_info    = cache_info     # type: ignore
        wrapper.stats         = stats          # type: ignore
        wrapper.cache         = cache          # type: ignore
        
        return wrapper  # type: ignore
    
    return decorator