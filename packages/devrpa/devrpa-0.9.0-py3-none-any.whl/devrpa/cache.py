
import os
import pickle
import hashlib
import time
import json
from abc import ABC, abstractmethod
from typing import Any, Optional, Union
from pathlib import Path

class CacheBackend(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 3600):
        pass

    @abstractmethod
    def delete(self, key: str):
        pass

    @abstractmethod
    def clear(self):
        pass

    @abstractmethod
    def stats(self) -> dict:
        pass

class MemoryCache(CacheBackend):
    def __init__(self):
        self._store = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            val, expire_at = self._store[key]
            if time.time() < expire_at:
                self._hits += 1
                return val
            else:
                del self._store[key]
        self._misses += 1
        return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        self._store[key] = (value, time.time() + ttl)

    def delete(self, key: str):
        if key in self._store:
            del self._store[key]

    def clear(self):
        self._store.clear()

    def stats(self) -> dict:
        return {"hits": self._hits, "misses": self._misses, "size": len(self._store)}

class FileCache(CacheBackend):
    def __init__(self, cache_dir: str = ".devrpa_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self._hits = 0
        self._misses = 0

    def _get_path(self, key: str) -> Path:
        # Sanitize key to be file safe
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.cache"

    def get(self, key: str) -> Optional[Any]:
        p = self._get_path(key)
        if p.exists():
            try:
                with open(p, "rb") as f:
                    data = pickle.load(f)
                    if time.time() < data["expire_at"]:
                        self._hits += 1
                        return data["value"]
                    else:
                        os.remove(p)
            except Exception:
                pass # Corrupt or error
        self._misses += 1
        return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        p = self._get_path(key)
        data = {
            "value": value,
            "expire_at": time.time() + ttl,
            "key": key # Store original key for debug
        }
        with open(p, "wb") as f:
            pickle.dump(data, f)

    def delete(self, key: str):
        p = self._get_path(key)
        if p.exists():
            os.remove(p)

    def clear(self):
        for p in self.cache_dir.glob("*.cache"):
            os.remove(p)

    def stats(self) -> dict:
        # Count files
        count = len(list(self.cache_dir.glob("*.cache")))
        return {"hits": self._hits, "misses": self._misses, "size": count}

def get_cache_backend(type: str = "file", **kwargs) -> CacheBackend:
    if type == "memory":
        return MemoryCache()
    elif type == "file":
        return FileCache(**kwargs)
    else:
        # Fallback or error
        return FileCache(**kwargs)
