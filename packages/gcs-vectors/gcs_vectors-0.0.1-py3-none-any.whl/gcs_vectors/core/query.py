import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
from .storage import GCSStorage
from .cache import VectorCache

class QueryEngine:
    def __init__(self, storage: GCSStorage, cache: VectorCache, centroids_path: str = "index/centroids.parquet", shards_prefix: str = "shards"):
        self.storage = storage
        self.cache = cache
        self.centroids_path = centroids_path
        self.shards_prefix = shards_prefix
        self.executor = ThreadPoolExecutor(max_workers=10)

    def _compute_similarity(self, query_v: np.ndarray, vectors: np.ndarray, metric: str = 'l2') -> np.ndarray:
        """Computes distances/similarities."""
        if metric == 'l2':
            return np.sum((vectors - query_v)**2, axis=1)
        elif metric == 'cosine':
            # cosine distance = 1 - (A.B / |A||B|)
            # Assuming vectors might not be normalized
            norm_q = np.linalg.norm(query_v)
            norm_v = np.linalg.norm(vectors, axis=1)
            dot = np.dot(vectors, query_v)
            # Clip for numerical stability
            similarity = dot / (norm_q * norm_v + 1e-10)
            return 1 - similarity
        return np.zeros(len(vectors))

    async def query(self, query_vector: np.ndarray, top_k: int = 5, nprobe: int = 3, metric: str = 'l2') -> List[Dict[str, Any]]:
        """
        1. Find nprobe clusters.
        2. Async fetch shards.
        3. Local scan.
        """
        # 1. Load centroids (Cached)
        df_centroids = self.cache.get_centroids(self.storage, self.centroids_path)
        centroids = df_centroids.drop(columns=['cluster_id']).values.astype(np.float32)
        
        # 2. Find nprobe nearest centroids
        query_v = query_vector.astype(np.float32)
        v_norm = np.sum(query_v**2)
        c_norm = np.sum(centroids**2, axis=1)
        dist_to_c = v_norm + c_norm - 2 * np.dot(centroids, query_v)
        nearest_clusters = np.argsort(dist_to_c)[:nprobe]
        
        # 3. Fetch shards for these clusters asynchronously
        tasks = []
        for cluster_id in nearest_clusters:
            prefix = f"{self.shards_prefix}/cluster_{cluster_id}/"
            # Get list of files in cluster
            files = self.storage.list_files(prefix)
            for f in files:
                # f is full path, we need relative or enough for read_parquet
                # gcsfs ls returns full paths.
                tasks.append(self._fetch_shard_async(f))
        
        shards_data = await asyncio.gather(*tasks)
        
        if not shards_data:
            return []
            
        all_df = pd.concat(shards_data, ignore_index=True)
        
        # 4. Local Similarity Scan
        # Vectors are stored as lists in 'vector' column
        vectors = np.stack(all_df['vector'].values).astype(np.float32)
        scores = self._compute_similarity(query_v, vectors, metric=metric)
        
        all_df['score'] = scores
        # Sort by score (ascending for distances)
        top_results = all_df.sort_values('score').head(top_k)
        
        return top_results[['id', 'score', 'metadata']].to_dict('records')

    async def _fetch_shard_async(self, path: str) -> pd.DataFrame:
        """Wrapper for async file fetching using thread pool."""
        loop = asyncio.get_event_loop()
        
        # gcsfs/fsspec ls returns bucket/prefix/path or /bucket/prefix/path
        # We need to strip everything up to our relative path
        path_str = str(path).lstrip('/')
        
        # Calculate the base path we should strip
        parts = [self.storage.bucket_name]
        if self.storage.prefix:
            parts.append(self.storage.prefix)
        
        base_prefix = "/".join(parts) + "/"
        
        if path_str.startswith(base_prefix):
            rel_path = path_str[len(base_prefix):]
        else:
            rel_path = path_str
            
        return await loop.run_in_executor(self.executor, self.cache.get_shard, self.storage, rel_path)
