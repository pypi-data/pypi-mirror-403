from typing import Any, Callable, Optional, Tuple, List

from .key_path_resolver import KeyPathResolver


class CacheKeyBuilder:
    """Construtor de chaves para cache com suporte a paths aninhados."""
    
    def __init__(
        self,
        func: Callable,
        key_args: Optional[List[str]],
        typed: bool,
        use_class_name: bool
    ):
        self.func = func
        self.key_args = key_args
        self.typed = typed
        self.use_class_name = use_class_name
        self._param_names = func.__code__.co_varnames[:func.__code__.co_argcount]

    def build(self, self_obj: Any, args: Tuple, kwargs: dict) -> Tuple:
        """Constrói chave de cache baseada nos argumentos."""
        try:
            if self.key_args is None:
                key = self._build_full_key(self_obj, args, kwargs)
            else:
                key = self._build_selective_key(self_obj, args, kwargs)
            
            if self.typed:
                key = self._add_type_info(key, args, kwargs)
            
            hash(key)  # Ensure hashable
            return key
            
        except TypeError as e:
            raise TypeError(f"Cache key contains unhashable type: {e}") from e

    def _build_full_key(self, self_obj: Any, args: Tuple, kwargs: dict) -> Tuple:
        """Constrói chave usando todos os argumentos."""
        self_key = self._get_self_key(self_obj)
        kwargs_tuple = tuple(sorted(kwargs.items())) if kwargs else ()
        return (self_key,) + args + kwargs_tuple

    def _build_selective_key(self, self_obj: Any, args: Tuple, kwargs: dict) -> Tuple:
        """Constrói chave usando apenas argumentos especificados."""
        args_dict = dict(zip(self._param_names[1:], args))
        args_dict.update(kwargs)
        
        self_key = self._get_self_key(self_obj)
        key_parts = [self_key]
        
        assert self.key_args is not None
        for arg_path in self.key_args:
            value = self._resolve_arg_path(arg_path, args_dict)
            key_parts.append(value)
        
        return tuple(key_parts)
    
    def _resolve_arg_path(self, arg_path: str, args_dict: dict) -> Any:
        """Resolve um path de argumento (simples ou aninhado)."""
        if '.' not in arg_path and '[' not in arg_path:
            # Simple argument
            if arg_path not in args_dict:
                raise KeyError(f"Argument '{arg_path}' not found")
            return args_dict[arg_path]
        
        # Nested path
        base_arg = arg_path.split('.')[0].split('[')[0]
        
        if base_arg not in args_dict:
            raise KeyError(f"Base argument '{base_arg}' not found")
        
        try:
            remaining_path = arg_path[len(base_arg):].lstrip('.')
            return KeyPathResolver.resolve(args_dict[base_arg], remaining_path)
        except (AttributeError, KeyError, IndexError) as e:
            raise KeyError(f"Cannot resolve path '{arg_path}': {e}") from e

    def _add_type_info(self, key: Tuple, args: Tuple, kwargs: dict) -> Tuple:
        """Adiciona informação de tipo à chave."""
        type_info = (
            tuple(type(arg).__name__ for arg in args) +
            tuple(type(v).__name__ for k, v in sorted(kwargs.items()))
        )
        return key + type_info
    
    def _get_self_key(self, self_obj: Any) -> str:
        """Gera chave estável ou por instância para self."""
        if self.use_class_name:
            return f"{self_obj.__class__.__module__}.{self_obj.__class__.__name__}"
        return str(id(self_obj))

