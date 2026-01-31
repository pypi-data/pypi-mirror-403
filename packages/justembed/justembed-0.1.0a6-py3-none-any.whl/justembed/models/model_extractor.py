"""
Model Extractor

Extracts and manages the bundled ONNX model.
"""

import os
import tarfile
from pathlib import Path
from typing import Optional


def get_cache_dir() -> Path:
    """
    Get the cache directory for JustEmbed.
    
    Returns:
        Path to cache directory (~/.cache/justembed/)
    """
    cache_dir = Path.home() / ".cache" / "justembed"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_bundled_model_path() -> Path:
    """
    Get path to bundled compressed model.
    
    Returns:
        Path to e5-small-int8.tar.gz in package
    """
    # Get the directory where this file is located
    models_dir = Path(__file__).parent
    return models_dir / "e5-small-int8.tar.gz"


def extract_model(force: bool = False) -> str:
    """
    Extract ONNX model from compressed format if needed.
    
    Args:
        force: If True, extract even if model already exists
    
    Returns:
        Path to extracted ONNX model file
    """
    cache_dir = get_cache_dir()
    model_path = cache_dir / "e5-small-int8.onnx"
    
    # Check if model already extracted
    if not force and model_path.exists():
        return str(model_path)
    
    # Extract model from bundled tar.gz
    bundled_path = get_bundled_model_path()
    
    if not bundled_path.exists():
        raise FileNotFoundError(
            f"Bundled model not found at {bundled_path}. "
            f"Package may be corrupted."
        )
    
    # Extract tar.gz to cache directory
    with tarfile.open(bundled_path, "r:gz") as tar:
        tar.extractall(path=cache_dir)
    
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model extraction failed. Expected {model_path} after extraction."
        )
    
    return str(model_path)


def get_model_path() -> str:
    """
    Get path to ONNX model, extracting if necessary.
    
    This is the main entry point for getting the model path.
    It will extract the model on first use and return the cached
    path on subsequent calls.
    
    Returns:
        Path to ONNX model file
    """
    return extract_model(force=False)
