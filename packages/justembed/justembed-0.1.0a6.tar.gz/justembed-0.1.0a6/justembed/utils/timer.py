"""
Timer Utility

Simple timer for tracking elapsed time during operations.
"""

import time


class Timer:
    """Simple timer for tracking elapsed time."""
    
    def __init__(self):
        """Initialize timer."""
        self._start_time: float = 0.0
    
    def start(self) -> None:
        """Start timing."""
        self._start_time = time.perf_counter()
    
    def elapsed(self) -> float:
        """
        Get elapsed time since start.
        
        Returns:
            Elapsed time in seconds
        """
        return time.perf_counter() - self._start_time
