import time
import pickle
import hashlib
import json
from threading import RLock
from typing import Any, Optional
from pathlib import Path

from .cache_backend import CacheBackend, MISSING


class FileSystemBackend(CacheBackend):
    """Backend de persistência em filesystem com auto-limpeza."""
    
    def __init__(
        self,
        cache_dir: str = ".cache",
        file_ttl_days: float = 7,
        auto_cleanup: bool = True
    ):
        self.cache_dir = Path(cache_dir)
        self.file_ttl_seconds = file_ttl_days * 86400
        self.auto_cleanup = auto_cleanup
        self._lock = RLock()
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / ".cache_metadata.json"
        self._metadata = self._load_metadata()
        
        if self.auto_cleanup:
            self.cleanup_expired()
    
    def _load_metadata(self) -> dict:
        """Carrega metadata de expiração."""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def _save_metadata(self) -> None:
        """Salva metadata de expiração."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self._metadata, f)
        except IOError:
            pass  # Non-critical failure
    
    def _get_file_path(self, key: str) -> Path:
        """Gera caminho do arquivo baseado na chave."""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"cache_{key_hash}.pkl"
    
    def _is_expired(self, file_path: Path) -> bool:
        """Verifica se arquivo está expirado."""
        key = file_path.name
        
        # Check metadata first
        if key in self._metadata:
            return time.time() > self._metadata[key]
        
        # Fallback to file timestamp
        try:
            mtime = file_path.stat().st_mtime
            return (time.time() - mtime) > self.file_ttl_seconds
        except OSError:
            return True
    
    def get(self, key: str) -> Optional[Any]:
        """Recupera valor do filesystem."""
        with self._lock:
            file_path = self._get_file_path(key)
            
            if not file_path.exists() or self._is_expired(file_path):
                if file_path.exists():
                    self.delete(key)
                return MISSING
            
            try:
                with open(file_path, 'rb') as f:
                    return pickle.load(f)
            except (pickle.PickleError, IOError, EOFError):
                self.delete(key)
                return MISSING
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Armazena valor no filesystem."""
        with self._lock:
            file_path = self._get_file_path(key)
            
            try:
                with open(file_path, 'wb') as f:
                    pickle.dump(value, f, protocol=pickle.HIGHEST_PROTOCOL)
                
                expiry_time = time.time() + (ttl or self.file_ttl_seconds)
                self._metadata[file_path.name] = expiry_time
                self._save_metadata()
            except (pickle.PickleError, IOError):
                if file_path.exists():
                    file_path.unlink()
    
    def delete(self, key: str) -> None:
        """Remove valor do filesystem."""
        with self._lock:
            file_path = self._get_file_path(key)
            
            if file_path.exists():
                try:
                    file_path.unlink()
                except OSError:
                    pass
            
            if file_path.name in self._metadata:
                del self._metadata[file_path.name]
                self._save_metadata()
    
    def clear(self) -> None:
        """Limpa todos os arquivos de cache."""
        with self._lock:
            for cache_file in self.cache_dir.glob("cache_*.pkl"):
                try:
                    cache_file.unlink()
                except OSError:
                    pass
            
            self._metadata.clear()
            self._save_metadata()
    
    def cleanup_expired(self) -> int:
        """Remove arquivos expirados. Retorna número de itens removidos."""
        with self._lock:
            removed_count = 0
            
            for cache_file in self.cache_dir.glob("cache_*.pkl"):
                if self._is_expired(cache_file):
                    try:
                        cache_file.unlink()
                        removed_count += 1
                        
                        if cache_file.name in self._metadata:
                            del self._metadata[cache_file.name]
                    except OSError:
                        pass
            
            if removed_count > 0:
                self._save_metadata()
            
            return removed_count
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do cache em disco."""
        with self._lock:
            cache_files   = list(self.cache_dir.glob("cache_*.pkl"))
            total_size    = sum(f.stat().st_size for f in cache_files if f.exists())
            expired_count = sum(1 for f in cache_files if self._is_expired(f))
            
            return {
                'total_files'      : len(cache_files),
                'expired_files'    : expired_count,
                'total_size_bytes' : total_size,
                'total_size_mb'    : round(total_size / (1024 * 1024), 2),
                'cache_dir'        : str(self.cache_dir.absolute())
            }

