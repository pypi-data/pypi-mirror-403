"""
JustEmbed - A semantic engine that just works.

Offline-first semantic search for everyday laptops.
"""

__version__ = "0.1.0a5"
__author__ = "Krishnamoorthy Sankaran"

# Import core functions
from justembed.core.loader import load
from justembed.core.indexer import embed
from justembed.core.searcher import search
from justembed.core.status import status, unload, clear_cache
from justembed.core.logger import set_verbose

# Import exceptions
from justembed.exceptions import (
    JustEmbedError,
    NotLoadedError,
    InvalidInputError,
    ChunkLimitError,
    TimeoutError
)

__all__ = [
    # Main functions (5)
    "load",
    "embed", 
    "search",
    "status",
    "unload",
    # Utility functions (2)
    "clear_cache",
    "set_verbose",
    # Exceptions
    "JustEmbedError",
    "NotLoadedError",
    "InvalidInputError",
    "ChunkLimitError",
    "TimeoutError",
    # Metadata
    "__version__"
]
