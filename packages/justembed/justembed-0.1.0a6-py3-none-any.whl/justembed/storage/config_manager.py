"""
Config Manager

Manages configuration JSON file.
"""

import os
import json
from typing import Dict, Any

from justembed.exceptions import InvalidInputError


def save_config(path: str, config: Dict[str, Any]) -> None:
    """
    Save configuration to JSON file.
    
    Args:
        path: Path to folder (will write to .justembed subfolder)
        config: Configuration dictionary
    """
    # Create .justembed directory if it doesn't exist
    justembed_dir = os.path.join(path, ".justembed")
    os.makedirs(justembed_dir, exist_ok=True)
    
    # Write to JSON file
    output_path = os.path.join(justembed_dir, "config.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)


def load_config(path: str) -> Dict[str, Any]:
    """
    Load configuration from JSON file.
    
    Args:
        path: Path to folder containing .justembed subfolder
        
    Returns:
        Configuration dictionary
        
    Raises:
        InvalidInputError: If config file doesn't exist
    """
    config_path = os.path.join(path, ".justembed", "config.json")
    
    if not os.path.exists(config_path):
        raise InvalidInputError(
            f"Config file not found: {config_path}"
        )
    
    # Read JSON file
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    return config
