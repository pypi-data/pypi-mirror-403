"""
Limit Enforcer

Enforces chunk and time limits to prevent resource exhaustion.
"""

import logging

from justembed.exceptions import ChunkLimitError, TimeoutError


logger = logging.getLogger(__name__)


def check_chunk_limit(estimated_chunks: int, limit: int) -> None:
    """
    Check if estimated chunks exceed system limit.
    
    Args:
        estimated_chunks: Estimated number of chunks to process
        limit: Maximum chunks allowed
        
    Raises:
        ChunkLimitError: If estimated chunks exceed limit
    """
    if estimated_chunks > limit:
        raise ChunkLimitError(
            chunks=estimated_chunks,
            limit=limit
        )


def enforce_time_limit(
    elapsed: float,
    soft_limit: float = 5.0,
    hard_limit: float = 30.0
) -> None:
    """
    Enforce time limits with warnings and errors.
    
    Note: These limits apply to actual work (embedding/search), not model loading.
    Model loading time is tracked separately and excluded from these limits.
    
    Args:
        elapsed: Elapsed time in seconds (excluding model load time)
        soft_limit: Soft limit for warnings (default: 5.0s)
        hard_limit: Hard limit for errors (default: 30.0s)
        
    Raises:
        TimeoutError: If elapsed time exceeds hard limit
    """
    if elapsed >= hard_limit:
        raise TimeoutError(elapsed=elapsed)
    elif elapsed >= soft_limit:
        logger.warning(
            f"Operation is taking longer than expected: {elapsed:.1f}s elapsed. "
            f"Consider indexing fewer files or smaller documents."
        )
