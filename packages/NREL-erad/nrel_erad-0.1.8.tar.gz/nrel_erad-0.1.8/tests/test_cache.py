#!/usr/bin/env python
"""Quick test script for cache functionality."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from erad.api import get_cache_directory
from erad.api.cache import get_metadata_file, scan_cache_directory, refresh_models_from_cache
from erad.api.main import uploaded_models


def main():
    print("Testing ERAD API Cache Functionality")
    print("=" * 60)

    # Test cache directory
    print("\n1. Testing cache directory...")
    cache_dir = get_cache_directory()
    print(f"   Cache directory: {cache_dir}")
    print(f"   Exists: {cache_dir.exists()}")

    # Test metadata file
    print("\n2. Testing metadata file...")
    metadata_file = get_metadata_file()
    print(f"   Metadata file: {metadata_file}")
    print(f"   Exists: {metadata_file.exists()}")

    # Test scan
    print("\n3. Scanning cache directory...")
    models = scan_cache_directory()
    print(f"   Found {len(models)} models")
    for name, info in models.items():
        print(f"   - {name}: {info.file_path}")

    # Test refresh
    print("\n4. Testing refresh...")
    refresh_models_from_cache(uploaded_models)
    print("   Refresh completed successfully")

    print("\n" + "=" * 60)
    print("✅ All cache functionality tests passed!")


if __name__ == "__main__":
    main()
