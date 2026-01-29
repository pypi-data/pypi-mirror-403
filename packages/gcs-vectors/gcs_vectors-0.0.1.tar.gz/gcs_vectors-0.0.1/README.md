# gcs-vectors

A lightweight, serverless-ready vector search library that uses **Google Cloud Storage (GCS)** with **Hierarchical Namespace (HNS)** as its primary storage engine.

## Features
- **Cost-Efficient**: Store millions of vectors on GCS using Parquet for columnar efficiency.
- **Fast Search**: IVF-Flat indexing with asynchronous shard fetching reduces latency.
- **Serverless Optimized**: Minimal memory footprint; only fetches what is necessary for the search.
- **HNS Native**: Leverages GCS Hierarchical Namespace for atomic sharding and metadata organization.

---

## Installation

```bash
pip install gcs-vectors
```

*Note: Depends on `gcsfs`, `pyarrow`, `numpy`, and `scipy`.*

---

## Getting Started

### 1. Initialize the Client
Point the client to your GCS bucket. You can provide a GCP project ID and authentication token (optional if your environment is already authenticated).

```python
from gcs_vectors import GCSVectors

# Initialize client with optional prefix and custom paths
client = GCSVectors(
    bucket_name="your-hns-enabled-bucket",
    prefix="v1/app-data",                 # Optional: namespace for all operations
    centroids_path="index/idx.parquet",    # Optional: custom path for centroids
    shards_path="data/vector_shards",     # Optional: custom path for vector shards
    project_id="your-gcp-project-id",
    token='google_default'
)
```

### 2. Create and Train a Vector Index
Before adding data, you need to train the index to generate centroids. This defines how your vectors will be sharded across the bucket.

```python
import numpy as np

# Generate some sample training data (e.g., 1000 vectors of 128 dims)
training_vectors = np.random.rand(1000, 128).astype(np.float32)

# Train the index with 100 clusters (centroids)
# This writes 'index/centroids.parquet' to your bucket
client.train(training_vectors, n_clusters=100)
```

### 3. Indexing a Markdown File
In a real-world scenario, you'll want to embed document content (using a model like OpenAI or `sentence-transformers`) and store it with its metadata.

```python
from sentence_transformers import SentenceTransformer
import os

# 1. Load your favorite embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Read your markdown file
file_path = "guides/getting-started.md"
with open(file_path, "r") as f:
    content = f.read()

# 3. Generate embedding
vector = model.encode(content).astype(np.float32)

# 4. Upsert into GCS
client.upsert(
    ids=[file_path], 
    vectors=np.array([vector]), 
    metadata=[{
        "filename": "getting-started.md",
        "content_preview": content[:200],
        "type": "documentation"
    }]
)
```

### 4. Search for Documents
Query the index asynchronously. The engine finds the nearest centroids, fetches only the relevant shards from GCS, and performs a local scan.

```python
import asyncio

async def run_search():
    # Embed your query
    query_text = "How do I get started with GCS?"
    query_vector = model.encode(query_text).astype(np.float32)

    # Search top 5 matches
    results = await client.search(
        query_vector, 
        top_k=5, 
        nprobe=3, 
        metric='cosine'
    )

    for match in results:
        print(f"File: {match['id']} | Score: {match['score']:.4f}")
        print(f"Snippet: {match['metadata']['content_preview']}...")

if __name__ == "__main__":
    asyncio.run(run_search())
```

---

## Indexing Existing Bucket Files

If your bucket already contains files (e.g., thousands of `.md` or `.pdf` files), `gcs-vectors` acts as a **Sidecar Index**. You don't need to move your files; you just create a vector index that points to them.

### Workflow: 
1. **Crawl**: List files in your existing directory.
2. **Embed**: Download and embed content locally.
3. **Index**: Upsert vectors using the GCS path as the `id`.

```python
# Helper Example: Indexing an existing 'docs/' folder in the same bucket
existing_docs = client.storage.list_files("docs/", recursive=True)

for file_path in existing_docs:
    if file_path.endswith(".md"):
        # 1. Read directly from GCS
        content = client.storage.cat(file_path).decode('utf-8')
        
        # 2. Embed
        vector = model.encode(content)
        
        # 3. Upsert using the GCS path as the ID
        # This keeps your original files intact while making them searchable
        client.upsert(
            ids=[file_path],
            vectors=np.array([vector]),
            metadata=[{"path": file_path, "size": len(content)}]
        )
```

### Why this works:
- **No Data Duplication**: Your original documents stay in their folders.
- **Path-as-ID**: When you search, the library returns the GCS path (the ID), which you can use to immediately fetch the original file.
- **Serverless Scaling**: The index (`shards/`) is optimized for search, separate from your document storage hierarchy.

- **Storage Engine**: Built on `gcsfs` and `pyarrow`. Uses 'Range' headers to optimize data egress.
- **Index Logic (IVF-Flat)**: Centroids are cached locally (LRU). Data is sharded into `shards/cluster_{N}/data_{UUID}.parquet`.
- **Atomic Sharding**: Uses HNS directory properties to ensure that shard updates are consistent and partial states aren't visible during queries.

---

## Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bucket_name` | `str` | - | Name of your GCS bucket. |
| `prefix` | `str` | `None` | Path prefix (namespace) within the bucket for all operations. |
| `centroids_path` | `str` | `index/centroids.parquet` | Relative path to store the index centroids. |
| `shards_path` | `str` | `shards` | Relative path to store the vector shards. |
| `project_id` | `str` | `None` | Your Google Cloud project ID. |
| `token` | `str` | `None` | Path to JSON creds or `'google_default'`. |
| `cache_size` | `int` | `100` | Number of shards/centroids to keep in local memory. |

---

## License
This project is distributed under the 
[Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0), see
[LICENSE](./LICENSE) for more information.

