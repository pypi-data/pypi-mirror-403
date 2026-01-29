import numpy as np
import pandas as pd
from scipy.cluster.vq import kmeans2
import uuid
from typing import List, Dict, Any, Optional
from .storage import GCSStorage

class IVFIndex:
    def __init__(self, storage: GCSStorage, centroids_path: str = "index/centroids.parquet", shards_prefix: str = "shards"):
        self.storage = storage
        self.centroids_path = centroids_path
        self.shards_prefix = shards_prefix

    def train(self, vectors: np.ndarray, n_clusters: int = 100):
        """
        Generates centroids using K-Means and saves to GCS.
        """
        # Ensure vectors are float32 for consistency
        data = vectors.astype(np.float32)
        
        # kmeans2 returns (centroids, label)
        centroids, _ = kmeans2(data, n_clusters, minit='points', iter=20)
        
        # Save centroids
        df_centroids = pd.DataFrame(centroids)
        # We can add a column for cluster ID if needed, but index works
        df_centroids['cluster_id'] = np.arange(len(centroids))
        
        self.storage.write_parquet(self.centroids_path, df_centroids)
        return centroids

    def _find_nearest_centroids(self, vectors: np.ndarray, centroids: np.ndarray) -> np.ndarray:
        """Finds the nearest centroid for each vector."""
        # Compute L2 distances
        # dist(v, c) = sqrt(sum((v-c)^2))
        # (v-c)^2 = v^2 + c^2 - 2vc
        v_norm = np.sum(vectors**2, axis=1)[:, np.newaxis]
        c_norm = np.sum(centroids**2, axis=1)
        dist = v_norm + c_norm - 2 * np.dot(vectors, centroids.T)
        return np.argmin(dist, axis=1)

    def upsert(self, ids: List[str], vectors: np.ndarray, metadata: List[Dict[str, Any]]):
        """
        Assigns vectors to clusters and writes to GCS shards.
        """
        # 1. Load centroids
        df_centroids = self.storage.read_parquet(self.centroids_path)
        centroids = df_centroids.drop(columns=['cluster_id']).values.astype(np.float32)
        
        # 2. Find clusters
        cluster_assignments = self._find_nearest_centroids(vectors.astype(np.float32), centroids)
        
        # 3. Group by cluster and write to shards
        for cluster_id in np.unique(cluster_assignments):
            mask = (cluster_assignments == cluster_id)
            cluster_ids = [ids[i] for i, m in enumerate(mask) if m]
            cluster_vectors = vectors[mask]
            cluster_metadata = [metadata[i] for i, m in enumerate(mask) if m]
            
            # Create a DataFrame for the shard
            # Store vectors as a nested list or multiple columns? 
            # Columnar efficiency: let's store vector as one column of type list or separate columns.
            # pyarrow handles list types well.
            df_shard = pd.DataFrame({
                'id': cluster_ids,
                'vector': cluster_vectors.tolist(),
                'metadata': [str(m) for m in cluster_metadata] # Store as stringified JSON or structured?
            })
            
            # Atomic sharding: write to a unique file in the cluster folder
            shard_id = uuid.uuid4().hex
            shard_path = f"{self.shards_prefix}/cluster_{cluster_id}/data_{shard_id}.parquet"
            self.storage.write_parquet(shard_path, df_shard)
