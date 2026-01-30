from typing import Any
import re


class KeyPathResolver:
    """Resolve caminhos aninhados em objetos (ex: 'user.addresses[0].city')."""
    
    INDEX_PATTERN = re.compile(r'^(.+?)\[(\d+)\]$')
    
    @classmethod
    def resolve(cls, obj: Any, path: str) -> Any:
        """Resolve um caminho aninhado em um objeto."""
        if not path:
            return obj
        
        current = obj
        for part in path.split('.'):
            current = cls._resolve_part(current, part, path)
        
        return current
    
    @classmethod
    def _resolve_part(cls, obj: Any, part: str, full_path: str) -> Any:
        """Resolve uma parte do caminho (atributo ou índice)."""
        match = cls.INDEX_PATTERN.match(part)
        
        if match:
            attr_name, index = match.groups()
            obj = cls._access_attr_or_key(obj, attr_name)
            return cls._access_index(obj, int(index), full_path)
        
        return cls._access_attr_or_key(obj, part)
    
    @staticmethod
    def _access_attr_or_key(obj: Any, key: str) -> Any:
        """Acessa atributo ou chave de dict."""
        # Check dict/list access FIRST
        if hasattr(obj, '__getitem__'):
            try:
                return obj[key]  # Try as dict key or list index first
            except (KeyError, TypeError, IndexError):
                pass  # Fall through to attribute access
        
        # Then check attributes
        if hasattr(obj, key):
            return getattr(obj, key)
        
        raise AttributeError(f"Cannot access '{key}' on {type(obj).__name__}")
    
    @staticmethod
    def _access_index(obj: Any, index: int, path: str) -> Any:
        """Acessa índice em sequência."""
        try:
            return obj[index]
        except (IndexError, KeyError, TypeError) as e:
            raise KeyError(f"Cannot access index [{index}] in path '{path}': {e}") from e

