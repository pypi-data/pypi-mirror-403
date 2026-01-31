"""
Status Manager

Provides status information and management functions.
"""

import os
from typing import Dict, Any

try:
    import polars as pl
except ImportError:
    raise ImportError(
        "polars is required. Install with: pip install polars"
    )

from justembed.core._state import get_state, reset_state


def status() -> Dict[str, Any]:
    """
    Get current status of JustEmbed.
    
    Returns:
        Dictionary with loaded, path, files_indexed, chunks_used,
        chunks_limit, query_cache_size
    """
    state = get_state()
    
    # Basic status
    result = {
        "loaded": state["loaded"],
        "path": state["path"],
        "files_indexed": 0,
        "chunks_used": 0,
        "chunks_limit": state.get("chunk_limit", 0),
        "query_cache_size": 0
    }
    
    # If loaded and has embeddings, get counts
    if state["loaded"] and state["embeddings_df"] is not None:
        embeddings_df = state["embeddings_df"]
        result["chunks_used"] = len(embeddings_df)
        result["files_indexed"] = embeddings_df.select("file").n_unique()
    
    # If loaded and has config, use config values
    if state["loaded"] and state["config"] is not None:
        config = state["config"]
        result["files_indexed"] = config.get("files_indexed", result["files_indexed"])
        result["chunks_limit"] = config.get("chunk_limit", result["chunks_limit"])
    
    # Count query cache entries
    if state["loaded"] and state["path"] is not None:
        query_cache_path = os.path.join(state["path"], ".justembed", "query_cache.parquet")
        if os.path.exists(query_cache_path):
            try:
                cache_df = pl.read_parquet(query_cache_path)
                result["query_cache_size"] = len(cache_df)
            except Exception:
                pass
    
    return result


def unload() -> None:
    """
    Unload current folder and clear state.
    """
    reset_state()


def clear_cache() -> None:
    """
    Clear query cache.
    """
    state = get_state()
    
    if state["loaded"] and state["path"] is not None:
        query_cache_path = os.path.join(state["path"], ".justembed", "query_cache.parquet")
        if os.path.exists(query_cache_path):
            try:
                os.remove(query_cache_path)
            except Exception:
                pass
