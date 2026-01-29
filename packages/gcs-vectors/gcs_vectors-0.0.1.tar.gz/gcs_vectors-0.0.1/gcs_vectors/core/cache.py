from functools import lru_cache
import pandas as pd
from typing import Optional
import threading

class VectorCache:
    def __init__(self, size: int = 128):
        self.size = size
        self._lock = threading.Lock()
        # We'll use a manual LRU if sophisticated, 
        # but for now, simple cache for dataframes.
        self._cache = {}

    def get_centroids(self, storage, path: str) -> pd.DataFrame:
        """Cached centroid retrieval."""
        key = f"centroids:{path}"
        with self._lock:
            if key in self._cache:
                return self._cache[key]
        
        df = storage.read_parquet(path)
        with self._lock:
            self._cache[key] = df
            # Simple eviction
            if len(self._cache) > self.size:
                self._cache.pop(next(iter(self._cache)))
        return df

    def get_shard(self, storage, path: str) -> pd.DataFrame:
        """Cached shard retrieval."""
        key = f"shard:{path}"
        with self._lock:
            if key in self._cache:
                return self._cache[key]
        
        # Optimization: Fetch only 'vector' if metadata not needed? 
        # The prompt says: "Fetch only 'vector' column ... if metadata isn't needed for first pass"
        # For query, we need IDs at least.
        df = storage.read_parquet(path)
        with self._lock:
            self._cache[key] = df
            if len(self._cache) > self.size:
                self._cache.pop(next(iter(self._cache)))
        return df
