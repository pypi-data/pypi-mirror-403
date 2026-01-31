"""
Example 1: Basic Usage - Load, Embed, Search

This example shows the simplest possible workflow:
1. Load a folder
2. Embed files (if not already indexed)
3. Search for something

This example MUST work before we ship v0.1.0.
"""

import justembed as je

# Step 1: Load a folder
# Expected output:
#   ✓ Loaded: sample_data/
#   ⚠ Not indexed yet. Run je.embed() to create index.
print("=" * 50)
print("Step 1: Load folder")
print("=" * 50)
result = je.load("sample_data/")
print(f"Status: {result['status']}")
print(f"Files found: {result['files_total']}")
print()

# Step 2: Embed files
# Expected output:
#   Checking limits... ✓ Safe (45 chunks estimated)
#   Embedding files... [████████████████] 100% (2.1s)
#   ✓ Indexed 3 files, 45 chunks
print("=" * 50)
print("Step 2: Embed files")
print("=" * 50)
result = je.embed()
print(f"Files embedded: {result['files_embedded']}")
print(f"Chunks created: {result['chunks_created']}")
print(f"Time taken: {result['time_taken']:.1f}s")
print()

# Step 3: Search
# Expected output:
#   Found 3 results in 0.04s
print("=" * 50)
print("Step 3: Search")
print("=" * 50)
results = je.search("fruits that are red in color", top_k=3)

for i, result in enumerate(results, 1):
    print(f"\n{i}. Score: {result['score']:.3f}")
    print(f"   File: {result['file']}")
    print(f"   Text: {result['text'][:100]}...")

# Expected final state:
# - .justembed/ folder created in sample_data/
# - embeddings.parquet exists
# - index.md exists
# - config.json exists
# - query_cache.parquet exists (after search)

print("\n" + "=" * 50)
print("✓ Example complete!")
print("=" * 50)
