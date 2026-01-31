"""
Loader

Loads folders and detects existing indexes.
"""

import os
from typing import Dict, Any

from justembed.utils.validator import validate_path, scan_text_files
from justembed.storage.parquet_reader import read_embeddings
from justembed.storage.config_manager import load_config
from justembed.core._state import update_state
from justembed.exceptions import InvalidInputError


def load(path: str) -> Dict[str, Any]:
    """
    Load folder or file for semantic search.
    
    Args:
        path: Path to folder or file
        
    Returns:
        Dictionary with status, files_total, indexed
        
    Raises:
        InvalidInputError: If path doesn't exist
    """
    # Validate path exists
    validate_path(path)
    
    # Check for .justembed/ subfolder
    justembed_dir = os.path.join(path, ".justembed")
    has_index = os.path.exists(justembed_dir) and os.path.isdir(justembed_dir)
    
    if has_index:
        # Load existing index
        try:
            embeddings_df = read_embeddings(path)
            config = load_config(path)
            
            # Update global state
            update_state(
                loaded=True,
                path=path,
                embeddings_df=embeddings_df,
                config=config
            )
            
            # Get file count from config or DataFrame
            files_indexed = config.get("files_indexed", 0)
            if files_indexed == 0:
                # Fallback: count unique files in DataFrame
                files_indexed = embeddings_df.select("file").n_unique()
            
            return {
                "status": "loaded",
                "files_total": files_indexed,
                "indexed": True
            }
        except Exception as e:
            # If loading fails, treat as not indexed
            has_index = False
    
    if not has_index:
        # Scan for text files
        text_files = scan_text_files(path)
        
        # Update global state (loaded but not indexed)
        update_state(
            loaded=True,
            path=path,
            embeddings_df=None,
            config=None
        )
        
        return {
            "status": "not_indexed",
            "files_total": len(text_files),
            "indexed": False
        }
