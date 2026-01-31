"""
Global State Management

Maintains global state for simple API without requiring users to manage objects.
"""

from typing import Any, Dict, Optional

# Global state dictionary
_state: Dict[str, Any] = {
    "loaded": False,
    "path": None,
    "embeddings_df": None,  # Polars DataFrame
    "config": None,
    "embedder": None,
    "chunk_limit": None,
}


def get_state() -> Dict[str, Any]:
    """
    Get current global state.
    
    Returns:
        Dictionary containing current state
    """
    return _state.copy()


def update_state(**kwargs: Any) -> None:
    """
    Update global state with provided values.
    
    Args:
        **kwargs: Key-value pairs to update in state
    """
    global _state
    for key, value in kwargs.items():
        if key in _state:
            _state[key] = value


def reset_state() -> None:
    """Reset global state to defaults."""
    global _state
    _state = {
        "loaded": False,
        "path": None,
        "embeddings_df": None,
        "config": None,
        "embedder": None,
        "chunk_limit": None,
    }
