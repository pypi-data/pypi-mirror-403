"""
Hardware Detector

Detects system capabilities and sets appropriate limits.
"""

try:
    import psutil
except ImportError:
    raise ImportError(
        "psutil is required. Install with: pip install psutil"
    )


def detect_system_ram() -> int:
    """
    Detect system RAM in GB.
    
    Returns:
        RAM in gigabytes (rounded down)
    """
    # Get total system memory in bytes
    total_memory = psutil.virtual_memory().total
    
    # Convert to GB (1 GB = 1024^3 bytes)
    ram_gb = total_memory / (1024 ** 3)
    
    # Round down to nearest GB
    return int(ram_gb)


def get_chunk_limit() -> int:
    """
    Calculate chunk limit based on system RAM.
    
    Rules:
    - < 4GB RAM: 10,000 chunks
    - 4-8GB RAM: 20,000 chunks
    - >= 8GB RAM: 30,000 chunks
    
    Returns:
        Maximum number of chunks allowed
    """
    ram_gb = detect_system_ram()
    
    if ram_gb < 4:
        return 10_000
    elif ram_gb < 8:
        return 20_000
    else:
        return 30_000
