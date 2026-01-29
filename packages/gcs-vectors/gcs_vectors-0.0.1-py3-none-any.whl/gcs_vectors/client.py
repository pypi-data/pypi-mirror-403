from typing import List, Dict, Any, Optional
import numpy as np
from .core.storage import GCSStorage
from .core.index import IVFIndex
from .core.query import QueryEngine
from .core.cache import VectorCache

class GCSVectors:
    def __init__(self, bucket_name: str, prefix: Optional[str] = None, 
                 centroids_path: str = "index/centroids.parquet", 
                 shards_path: str = "shards",
                 project_id: Optional[str] = None, 
                 token: Optional[str] = None, 
                 fs: Optional[Any] = None):
        """
        GCS-Vectors Client.
        """
        self.storage = GCSStorage(bucket_name, prefix=prefix, project_id=project_id, token=token, fs=fs)
        self.index = IVFIndex(self.storage, centroids_path=centroids_path, shards_prefix=shards_path)
        self.cache = VectorCache(size=100)
        self.query_engine = QueryEngine(self.storage, self.cache, centroids_path=centroids_path, shards_prefix=shards_path)

    def train(self, vectors: np.ndarray, n_clusters: int = 100):
        """Trains the IVF index with centroids."""
        return self.index.train(vectors, n_clusters)

    def upsert(self, ids: List[str], vectors: np.ndarray, metadata: Optional[List[Dict[str, Any]]] = None):
        """Adds or updates vectors in the index."""
        if metadata is None:
            metadata = [{} for _ in ids]
        return self.index.upsert(ids, vectors, metadata)

    async def search(self, query_vector: np.ndarray, top_k: int = 5, nprobe: int = 3, metric: str = 'l2'):
        """Searches for nearest vectors."""
        return await self.query_engine.query(query_vector, top_k, nprobe, metric)
