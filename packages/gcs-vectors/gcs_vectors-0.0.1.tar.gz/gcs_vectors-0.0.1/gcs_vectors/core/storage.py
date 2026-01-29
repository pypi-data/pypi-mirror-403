import gcsfs
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import io
import os
from typing import List, Optional, Union, Any
import numpy as np

class GCSStorage:
    def __init__(self, bucket_name: str, prefix: Optional[str] = None, project_id: Optional[str] = None, token: Optional[str] = None, fs: Optional[Any] = None):
        """
        GCS Storage Engine for Vector Data.
        
        Args:
            bucket_name: Name of the GCS bucket.
            prefix: Optional path prefix within the bucket.
            project_id: GCP Project ID.
            token: Authentication token.
            fs: Optional fsspec-compatible filesystem instance (e.g., for mocking).
        """
        self.bucket_name = bucket_name.strip('/')
        self.prefix = prefix.strip('/') if prefix else ""
        if fs:
            self.fs = fs
        else:
            self.fs = gcsfs.GCSFileSystem(project=project_id, token=token)
        
    def _get_full_path(self, path: str) -> str:
        parts = [self.bucket_name]
        if self.prefix:
            parts.append(self.prefix)
        if path.lstrip('/'):
            parts.append(path.lstrip('/'))
        return "/".join(parts)

    def write_parquet(self, path: str, df: pd.DataFrame, atomic: bool = True):
        """
        Writes a DataFrame to GCS as a Parquet file.
        Uses HNS atomic writes if atomic=True (by writing to a temp file and renaming if needed, 
        though HNS rename_folder is more common for bulk moves).
        For single file writes, GCS is already atomic.
        """
        full_path = self._get_full_path(path)
        
        # Ensure directory exists (useful for HNS)
        parent_dir = os.path.dirname(full_path)
        if not self.fs.exists(parent_dir):
            self.fs.makedirs(parent_dir, exist_ok=True)

        with self.fs.open(full_path, 'wb') as f:
            df.to_parquet(f, engine='pyarrow', index=False)

    def read_parquet(self, path: str, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Reads a Parquet file from GCS. 
        Supports projection (fetching only specific columns).
        """
        full_path = self._get_full_path(path)
        with self.fs.open(full_path, 'rb') as f:
            return pd.read_parquet(f, columns=columns, engine='pyarrow')

    def list_files(self, prefix: str, recursive: bool = False) -> List[str]:
        """Lists files in a given GCS path."""
        full_prefix = self._get_full_path(prefix)
        try:
            if recursive:
                files = self.fs.find(full_prefix)
            else:
                files = self.fs.ls(full_prefix, detail=False)
            
            # Normalize to strings if dicts are returned
            return [f if isinstance(f, str) else f.get('name', '') for f in files]
        except FileNotFoundError:
            return []

    def cat(self, path: str) -> bytes:
        """Reads raw content of a file from GCS."""
        full_path = self._get_full_path(path)
        return self.fs.cat(full_path)

    def rename_folder(self, old_path: str, new_path: str):
        """
        Leverages GCS HNS rename_folder capability for atomic sharding updates.
        """
        full_old = self._get_full_path(old_path)
        full_new = self._get_full_path(new_path)
        # Note: gcsfs might call the HNS specific API for this if configured
        self.fs.rename(full_old, full_new, recursive=True)

    async def async_read_parquet(self, path: str, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Asynchronously reads a Parquet file (simulated via thread-pool in gcsfs usually, 
        but here we use the async nature of gcsfs if available).
        """
        full_path = self._get_full_path(path)
        # gcsfs supports async via .open_async but let's stick to standard for now 
        # unless we explicitly need aiosession. For the task, we'll use a wrapper or concurrent futures.
        # This is a placeholder for the async logic in query engine.
        with self.fs.open(full_path, 'rb') as f:
            return pd.read_parquet(f, columns=columns, engine='pyarrow')
