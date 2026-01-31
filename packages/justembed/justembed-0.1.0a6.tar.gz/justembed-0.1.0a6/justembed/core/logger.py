"""
Logger

Centralized logging for JustEmbed operations with timing transparency.
"""

import logging
from typing import Optional


# Configure logger
logger = logging.getLogger("justembed")
logger.setLevel(logging.INFO)

# Create console handler if not already present
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('[JustEmbed] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def log_model_loading(elapsed: float) -> None:
    """
    Log model loading time.
    
    Args:
        elapsed: Time taken to load model in seconds
    """
    logger.info(f"Loading model... ({elapsed:.2f}s)")


def log_model_already_loaded() -> None:
    """Log that model is already loaded (no time needed)."""
    logger.info("Model already loaded (N/A)")


def log_embedding_start(file_count: int, chunk_count: int) -> None:
    """
    Log start of embedding operation.
    
    Args:
        file_count: Number of files to embed
        chunk_count: Number of chunks to embed
    """
    logger.info(f"Embedding {file_count} file(s) ({chunk_count} chunk(s))...")


def log_embedding_complete(elapsed: float) -> None:
    """
    Log completion of embedding operation.
    
    Args:
        elapsed: Time taken for embedding in seconds
    """
    logger.info(f"Embedding complete ({elapsed:.2f}s)")


def log_search_start(query: str) -> None:
    """
    Log start of search operation.
    
    Args:
        query: Search query text
    """
    # Truncate long queries for logging
    display_query = query if len(query) <= 50 else query[:47] + "..."
    logger.info(f"Searching for: \"{display_query}\"")


def log_search_complete(elapsed: float, result_count: int, cached: bool = False) -> None:
    """
    Log completion of search operation.
    
    Args:
        elapsed: Time taken for search in seconds
        result_count: Number of results returned
        cached: Whether query embedding was cached
    """
    cache_note = " (cached)" if cached else ""
    logger.info(f"Search complete{cache_note} ({elapsed:.2f}s) - {result_count} result(s)")


def log_warning(message: str) -> None:
    """
    Log a warning message.
    
    Args:
        message: Warning message
    """
    logger.warning(message)


def log_info(message: str) -> None:
    """
    Log an info message.
    
    Args:
        message: Info message
    """
    logger.info(message)


# Global verbose flag
_verbose = True


def set_verbose(verbose: bool) -> None:
    """
    Enable or disable verbose logging.
    
    Args:
        verbose: True to enable logging, False to disable
    """
    global _verbose
    _verbose = verbose
    
    if verbose:
        logger.setLevel(logging.INFO)
        for handler in logger.handlers:
            handler.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)
        for handler in logger.handlers:
            handler.setLevel(logging.WARNING)


def is_verbose() -> bool:
    """
    Check if verbose logging is enabled.
    
    Returns:
        True if verbose logging is enabled
    """
    return _verbose
