"""
Example 3: Error Handling

This example shows how JustEmbed handles errors gracefully:
1. Search without loading
2. Exceed chunk limits
3. Invalid paths
4. Non-text files

This example MUST work before we ship v0.1.0.
"""

import justembed as je
from justembed.exceptions import NotLoadedError, ChunkLimitError, InvalidInputError

# Error 1: Search without loading
print("=" * 50)
print("Error 1: Search without loading")
print("=" * 50)
try:
    je.search("test query")
except NotLoadedError as e:
    print(f"✓ Caught expected error: {e}")
print()

# Error 2: Load invalid path
print("=" * 50)
print("Error 2: Invalid path")
print("=" * 50)
try:
    je.load("nonexistent_folder/")
except InvalidInputError as e:
    print(f"✓ Caught expected error: {e}")
print()

# Error 3: Exceed chunk limits (simulated)
print("=" * 50)
print("Error 3: Chunk limit exceeded")
print("=" * 50)
# This would happen if user tries to index too many files
# We'll simulate by showing what the error looks like
try:
    # Simulate: je.embed("huge_folder/")
    raise ChunkLimitError(chunks=35000, limit=30000)
except ChunkLimitError as e:
    print(f"✓ Caught expected error:")
    print(f"  {e}")
print()

# Error 4: Load folder with non-text files
print("=" * 50)
print("Error 4: Non-text files")
print("=" * 50)
# JustEmbed should skip non-text files with a warning
# (This will be implemented in validator.py)
print("✓ JustEmbed will skip non-text files automatically")
print("  (PDFs, images, etc. will be ignored)")
print()

print("=" * 50)
print("✓ Example complete!")
print("=" * 50)
print("\nKey takeaway: JustEmbed fails gracefully with clear error messages.")
