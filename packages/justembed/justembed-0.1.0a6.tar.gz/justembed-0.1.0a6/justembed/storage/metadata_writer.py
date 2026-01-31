"""
Metadata Writer

Generates human-readable index metadata.
"""

import os


def write_metadata(
    path: str,
    files_count: int,
    chunks_count: int,
    timestamp: str,
    chunk_limit: int = 30000
) -> None:
    """
    Write index.md metadata file.
    
    Args:
        path: Path to folder (will write to .justembed subfolder)
        files_count: Number of files indexed
        chunks_count: Number of chunks created
        timestamp: ISO format timestamp
        chunk_limit: Maximum chunks allowed (default: 30000)
    """
    # Create .justembed directory if it doesn't exist
    justembed_dir = os.path.join(path, ".justembed")
    os.makedirs(justembed_dir, exist_ok=True)
    
    # Generate markdown content
    content = f"""# JustEmbed Index

- **Created**: {timestamp}
- **Model**: multilingual-e5-small
- **Files Indexed**: {files_count:,}
- **Chunks Created**: {chunks_count:,}
- **Chunk Limit**: {chunk_limit:,}
"""
    
    # Write to file
    output_path = os.path.join(justembed_dir, "index.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
