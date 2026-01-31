"""
Indexer

Creates embeddings and saves to disk.
"""

from typing import Dict, Any
from datetime import datetime

from justembed.exceptions import NotLoadedError
from justembed.core._state import get_state, update_state
from justembed.utils.validator import scan_text_files, read_text_file
from justembed.utils.text_chunker import chunk_text
from justembed.utils.limit_enforcer import check_chunk_limit
from justembed.utils.hardware_detector import get_chunk_limit
from justembed.utils.timer import Timer
from justembed.core.embedder import Embedder
from justembed.storage.parquet_writer import write_embeddings
from justembed.storage.metadata_writer import write_metadata
from justembed.storage.config_manager import save_config
from justembed.core.logger import (
    log_model_loading,
    log_model_already_loaded,
    log_embedding_start,
    log_embedding_complete
)


def embed() -> Dict[str, Any]:
    """
    Generate embeddings for loaded folder.
    
    Returns:
        Dictionary with files_embedded, chunks_created, time_taken, model_load_time
        
    Raises:
        NotLoadedError: If no folder is loaded
        ChunkLimitError: If estimated chunks exceed limit
    """
    # Check if folder is loaded
    state = get_state()
    if not state["loaded"] or state["path"] is None:
        raise NotLoadedError()
    
    path = state["path"]
    
    # Scan for text files
    text_files = scan_text_files(path)
    
    # Chunk all text files
    all_chunks = []
    for file_path in text_files:
        try:
            text = read_text_file(file_path)
            file_chunks = chunk_text(file_path, text)
            all_chunks.extend(file_chunks)
        except Exception:
            # Skip files that can't be read
            continue
    
    # Get chunk limit
    chunk_limit = state.get("chunk_limit")
    if chunk_limit is None:
        chunk_limit = get_chunk_limit()
        update_state(chunk_limit=chunk_limit)
    
    # Check chunk limit
    check_chunk_limit(len(all_chunks), chunk_limit)
    
    # Initialize embedder if not already initialized (track model loading time separately)
    model_load_time = 0.0
    embedder = state.get("embedder")
    if embedder is None:
        # Model needs to be loaded - track this time separately
        model_timer = Timer()
        model_timer.start()
        embedder = Embedder()
        model_load_time = model_timer.elapsed()
        log_model_loading(model_load_time)
        update_state(embedder=embedder)
    else:
        # Model already loaded
        log_model_already_loaded()
    
    # Log embedding start
    log_embedding_start(len(text_files), len(all_chunks))
    
    # Start timer for actual embedding work (AFTER model loading)
    work_timer = Timer()
    work_timer.start()
    
    # For large datasets, process in batches to avoid memory issues
    # Use generator-based approach for memory efficiency
    batch_size = 100  # Process 100 chunks at a time
    
    if len(all_chunks) > 500:
        # Memory-efficient approach for large datasets
        all_embeddings = []
        texts = [chunk["text"] for chunk in all_chunks]
        
        for embedding_batch in embedder.embed_batch_generator(texts, batch_size=batch_size):
            all_embeddings.extend(embedding_batch)
    else:
        # Original approach for small datasets (faster, less overhead)
        texts = [chunk["text"] for chunk in all_chunks]
        all_embeddings = embedder.embed_batch(texts)
    
    # Get work elapsed time
    work_elapsed = work_timer.elapsed()
    
    # Save embeddings
    write_embeddings(path, all_chunks, all_embeddings)
    
    # Generate metadata
    timestamp = datetime.now().isoformat()
    write_metadata(
        path,
        files_count=len(text_files),
        chunks_count=len(all_chunks),
        timestamp=timestamp,
        chunk_limit=chunk_limit
    )
    
    # Save config
    config = {
        "version": "0.1.0",
        "model_name": "e5-small",
        "chunk_limit": chunk_limit,
        "created_at": timestamp,
        "files_indexed": len(text_files),
        "chunks_created": len(all_chunks)
    }
    save_config(path, config)
    
    # Update global state
    from justembed.storage.parquet_reader import read_embeddings
    embeddings_df = read_embeddings(path)
    update_state(
        embeddings_df=embeddings_df,
        config=config
    )
    
    # Log completion
    log_embedding_complete(work_elapsed)
    
    # Total time includes model loading + work
    total_time = model_load_time + work_elapsed
    
    return {
        "files_embedded": len(text_files),
        "chunks_created": len(all_chunks),
        "time_taken": work_elapsed,  # Only embedding work time
        "model_load_time": model_load_time,  # Separate model loading time
        "total_time": total_time  # Total time including model load
    }
