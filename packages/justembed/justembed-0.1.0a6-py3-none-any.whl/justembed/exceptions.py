"""
JustEmbed Exception Classes

Custom exceptions for clear error handling and messaging.
"""


class JustEmbedError(Exception):
    """Base exception for all JustEmbed errors."""
    pass


class NotLoadedError(JustEmbedError):
    """Raised when operations require a loaded folder but none is loaded."""
    
    def __init__(self, message: str = "No folder loaded. Call je.load(path) first."):
        self.message = message
        super().__init__(self.message)


class InvalidInputError(JustEmbedError):
    """Raised when input validation fails."""
    pass


class ChunkLimitError(JustEmbedError):
    """Raised when chunk count exceeds system limits."""
    
    def __init__(self, chunks: int, limit: int):
        self.chunks = chunks
        self.limit = limit
        self.message = (
            f"Chunk limit exceeded: {chunks:,} chunks estimated, "
            f"limit is {limit:,}. Try indexing fewer files."
        )
        super().__init__(self.message)


class TimeoutError(JustEmbedError):
    """Raised when operations exceed time limits."""
    
    def __init__(self, elapsed: float):
        self.elapsed = elapsed
        self.message = (
            f"Embedding timed out after {elapsed:.1f}s. "
            f"Try indexing fewer files or smaller documents."
        )
        super().__init__(self.message)
