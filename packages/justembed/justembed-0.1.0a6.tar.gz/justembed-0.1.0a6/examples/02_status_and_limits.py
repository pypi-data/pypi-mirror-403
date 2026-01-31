"""
Example 2: Status and Limits

This example shows:
1. Checking status
2. Understanding limits
3. Clearing cache
4. Unloading

This example MUST work before we ship v0.1.0.
"""

import justembed as je

# Load folder
je.load("sample_data/")
je.embed()

# Check status
print("=" * 50)
print("Status Check")
print("=" * 50)
status = je.status()
print(f"Loaded: {status['loaded']}")
print(f"Path: {status['path']}")
print(f"Files indexed: {status['files_indexed']}")
print(f"Chunks used: {status['chunks_used']:,}/{status['chunks_limit']:,}")
print(f"Chunks remaining: {status['chunks_limit'] - status['chunks_used']:,}")
print(f"Query cache size: {status['query_cache_size']}")
print()

# Run some searches to populate cache
print("=" * 50)
print("Running searches...")
print("=" * 50)
je.search("red fruits")
je.search("vegetables")
je.search("healthy food")
print("✓ 3 searches completed")
print()

# Check status again
print("=" * 50)
print("Status After Searches")
print("=" * 50)
status = je.status()
print(f"Query cache size: {status['query_cache_size']}")
print()

# Clear cache
print("=" * 50)
print("Clearing Cache")
print("=" * 50)
je.clear_cache()
print("✓ Cache cleared")
print()

# Check status again
status = je.status()
print(f"Query cache size: {status['query_cache_size']}")
print()

# Unload
print("=" * 50)
print("Unloading")
print("=" * 50)
je.unload()
print("✓ Folder unloaded")
print()

# Try to check status (should show not loaded)
status = je.status()
print(f"Loaded: {status['loaded']}")

print("\n" + "=" * 50)
print("✓ Example complete!")
print("=" * 50)
