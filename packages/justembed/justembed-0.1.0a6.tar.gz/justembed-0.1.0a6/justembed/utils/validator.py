"""
Validator

Validates inputs and file types.
"""

import os
from pathlib import Path
from typing import List

from justembed.exceptions import InvalidInputError


# Accepted text file extensions
TEXT_EXTENSIONS = {
    '.txt', '.md', '.rst', '.log', '.csv', 
    '.json', '.xml', '.html', '.htm'
}


def validate_path(path: str) -> None:
    """
    Validate that path exists.
    
    Args:
        path: Path to validate
        
    Raises:
        InvalidInputError: If path doesn't exist
    """
    if not os.path.exists(path):
        raise InvalidInputError(f"Path does not exist: {path}")


def is_text_file(file_path: str) -> bool:
    """
    Check if file is a text file based on extension.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if text file, False otherwise
    """
    path = Path(file_path)
    extension = path.suffix.lower()
    return extension in TEXT_EXTENSIONS


def scan_text_files(path: str) -> List[str]:
    """
    Scan folder for text files recursively.
    
    Args:
        path: Folder path to scan
        
    Returns:
        List of text file paths (relative to input path)
        
    Raises:
        InvalidInputError: If path doesn't exist or is not a directory
    """
    validate_path(path)
    
    path_obj = Path(path)
    
    # If it's a file, return it if it's a text file
    if path_obj.is_file():
        if is_text_file(str(path_obj)):
            return [str(path_obj)]
        else:
            return []
    
    # If it's not a directory, raise error
    if not path_obj.is_dir():
        raise InvalidInputError(f"Path is not a file or directory: {path}")
    
    # Scan directory recursively
    text_files = []
    
    for root, dirs, files in os.walk(path):
        # Skip hidden directories (like .justembed, .git, etc.)
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            # Skip hidden files
            if file.startswith('.'):
                continue
            
            file_path = os.path.join(root, file)
            
            if is_text_file(file_path):
                text_files.append(file_path)
    
    return text_files


def read_text_file(file_path: str) -> str:
    """
    Read text file with automatic encoding detection.
    
    Args:
        file_path: Path to text file
        
    Returns:
        File content as string
        
    Raises:
        InvalidInputError: If file cannot be read
    """
    # Try common encodings
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue
    
    # If all encodings fail, raise error
    raise InvalidInputError(
        f"Could not read file {file_path}. "
        f"File may be binary or use an unsupported encoding."
    )
