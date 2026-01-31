"""
Parquet Reader

Reads embeddings from Parquet format using Polars.
"""

import os

try:
    import polars as pl
except ImportError:
    raise ImportError(
        "polars is required. Install with: pip install polars"
    )

from justembed.exceptions import InvalidInputError


def read_embeddings(path: str) -> pl.DataFrame:
    """
    Read embeddings from parquet file.
    
    Args:
        path: Path to folder containing .justembed subfolder
        
    Returns:
        Polars DataFrame with embeddings
        
    Raises:
        InvalidInputError: If embeddings file doesn't exist
    """
    embeddings_path = os.path.join(path, ".justembed", "embeddings.parquet")
    
    if not os.path.exists(embeddings_path):
        raise InvalidInputError(
            f"Embeddings file not found: {embeddings_path}"
        )
    
    # Read parquet file using Polars
    df = pl.read_parquet(embeddings_path)
    
    return df
