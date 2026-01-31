"""
Parquet Writer

Writes embeddings to Parquet format using Polars.
"""

import os
from typing import List, Dict, Any

try:
    import polars as pl
except ImportError:
    raise ImportError(
        "polars is required. Install with: pip install polars"
    )


def write_embeddings(
    path: str,
    chunks: List[Dict[str, Any]],
    embeddings: List[List[float]]
) -> None:
    """
    Write embeddings to parquet file.
    
    Args:
        path: Path to folder (will create .justembed subfolder)
        chunks: List of chunk metadata (file, chunk_id, text)
        embeddings: List of embedding vectors
        
    Raises:
        ValueError: If chunks and embeddings lengths don't match
    """
    if len(chunks) != len(embeddings):
        raise ValueError(
            f"Chunks and embeddings length mismatch: "
            f"{len(chunks)} chunks, {len(embeddings)} embeddings"
        )
    
    # Create .justembed directory if it doesn't exist
    justembed_dir = os.path.join(path, ".justembed")
    os.makedirs(justembed_dir, exist_ok=True)
    
    # Prepare data for DataFrame
    data = {
        "file": [chunk["file"] for chunk in chunks],
        "chunk_id": [chunk["chunk_id"] for chunk in chunks],
        "text": [chunk["text"] for chunk in chunks],
        "embedding": embeddings
    }
    
    # Create Polars DataFrame
    df = pl.DataFrame(data)
    
    # Write to parquet with compression
    output_path = os.path.join(justembed_dir, "embeddings.parquet")
    df.write_parquet(output_path, compression="snappy")
