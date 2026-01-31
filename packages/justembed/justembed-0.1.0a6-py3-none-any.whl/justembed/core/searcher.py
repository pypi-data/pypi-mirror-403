"""
Searcher

Executes semantic search queries.
"""

import os
from typing import List, Dict, Any

try:
    import polars as pl
    import numpy as np
except ImportError:
    raise ImportError(
        "polars and numpy are required. Install with: pip install polars numpy"
    )

from justembed.exceptions import NotLoadedError
from justembed.core._state import get_state
from justembed.utils.timer import Timer
from justembed.core.logger import (
    log_model_loading,
    log_model_already_loaded,
    log_search_start,
    log_search_complete
)


def search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Search indexed documents semantically.
    
    Args:
        query: Natural language search query
        top_k: Number of results to return (default: 5)
        
    Returns:
        List of results with score, file, text
        
    Raises:
        NotLoadedError: If no folder is loaded or no embeddings exist
    """
    # Log search start
    log_search_start(query)
    
    # Start timer for search operation
    search_timer = Timer()
    search_timer.start()
    
    # Check if folder is loaded
    state = get_state()
    if not state["loaded"] or state["path"] is None:
        raise NotLoadedError()
    
    # Check if embeddings exist
    if state["embeddings_df"] is None:
        raise NotLoadedError("No embeddings found. Call je.embed() first.")
    
    path = state["path"]
    embeddings_df = state["embeddings_df"]
    
    # Check query cache
    query_cache_path = os.path.join(path, ".justembed", "query_cache.parquet")
    query_embedding = None
    query_was_cached = False
    
    if os.path.exists(query_cache_path):
        try:
            cache_df = pl.read_parquet(query_cache_path)
            # Look for matching query
            matching = cache_df.filter(pl.col("query") == query)
            if len(matching) > 0:
                query_embedding = matching.row(0, named=True)["embedding"]
                query_was_cached = True
        except Exception:
            # If cache read fails, regenerate
            pass
    
    # If not cached, embed query
    model_load_time = 0.0
    if query_embedding is None:
        embedder = state.get("embedder")
        if embedder is None:
            # Model needs to be loaded
            model_timer = Timer()
            model_timer.start()
            from justembed.core.embedder import Embedder
            embedder = Embedder()
            model_load_time = model_timer.elapsed()
            log_model_loading(model_load_time)
            from justembed.core._state import update_state
            update_state(embedder=embedder)
        else:
            # Model already loaded
            log_model_already_loaded()
        
        query_embedding = embedder.embed_text(query)
        
        # Save to cache
        from datetime import datetime
        cache_data = {
            "query": [query],
            "embedding": [query_embedding],
            "timestamp": [datetime.now().isoformat()]
        }
        cache_df_new = pl.DataFrame(cache_data)
        
        # Append to existing cache or create new
        if os.path.exists(query_cache_path):
            try:
                cache_df_existing = pl.read_parquet(query_cache_path)
                cache_df_combined = pl.concat([cache_df_existing, cache_df_new])
                cache_df_combined.write_parquet(query_cache_path, compression="snappy")
            except Exception:
                cache_df_new.write_parquet(query_cache_path, compression="snappy")
        else:
            os.makedirs(os.path.dirname(query_cache_path), exist_ok=True)
            cache_df_new.write_parquet(query_cache_path, compression="snappy")
    
    # Compute cosine similarity
    query_vec = np.array(query_embedding, dtype=np.float32)
    # Ensure query vector is 1D with shape (384,)
    if query_vec.ndim > 1:
        query_vec = query_vec.flatten()
    if len(query_vec) != 384:
        query_vec = query_vec[:384]  # Take first 384 dims
    
    # Extract embeddings from DataFrame
    doc_embeddings = embeddings_df.select("embedding").to_series().to_list()
    
    # Compute similarities
    similarities = []
    for doc_emb in doc_embeddings:
        # doc_emb should be a list of floats
        # Convert to numpy array carefully
        if isinstance(doc_emb, list):
            doc_vec = np.array(doc_emb, dtype=np.float32)
        else:
            doc_vec = np.array(doc_emb, dtype=np.float32)
        
        # Ensure 1D with shape (384,)
        if doc_vec.ndim > 1:
            doc_vec = doc_vec.flatten()
        if len(doc_vec) != 384:
            doc_vec = doc_vec[:384]  # Take first 384 dims
        
        # Cosine similarity (vectors are already normalized)
        similarity = float(np.dot(query_vec, doc_vec))
        similarities.append(similarity)
    
    # Add similarity scores to DataFrame
    df_with_scores = embeddings_df.with_columns(
        pl.Series("score", similarities)
    )
    
    # Sort by score descending
    df_sorted = df_with_scores.sort("score", descending=True)
    
    # Get top-k results
    df_top_k = df_sorted.head(top_k)
    
    # Convert to list of dictionaries
    results = []
    for row in df_top_k.iter_rows(named=True):
        results.append({
            "score": row["score"],
            "file": row["file"],
            "text": row["text"]
        })
    
    # Calculate search time (excluding model load time)
    search_elapsed = search_timer.elapsed() - model_load_time
    
    # Log search complete
    log_search_complete(search_elapsed, len(results), cached=query_was_cached)
    
    return results
