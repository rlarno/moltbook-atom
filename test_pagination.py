#!/usr/bin/env python3
"""
Test script for Moltbook pagination system.
Validates blockchain-like feed pagination.
"""

import json
import sys
import subprocess
from pathlib import Path
from typing import List


def run_program(cmd: List[str]):
    """Run a program with arguments and return output."""
    result = subprocess.run(
        cmd,
        shell=False,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def test_pagination_basic():
    """Test basic pagination functionality."""
    print("Testing basic pagination...")
    
    # Test submolt pagination
    code, stdout, stderr = run_program([
        "python", "pagination_manager.py",
        "example-submolt-feed.json",
        "test-submolt",
        "/tmp/test-pagination",
        "2"
    ])
    
    if code != 0:
        print(f"❌ Pagination failed!")
        print(f"STDERR: {stderr}")
        return False
    
    # Check that files were created
    test_dir = Path("/tmp/test-pagination")
    wellknown = test_dir / "test-submolt.json"
    
    if not wellknown.exists():
        print(f"❌ Well-known file not created!")
        return False
    
    with open(wellknown, 'r') as f:
        wellknown_data = json.load(f)
    
    # Verify well-known structure
    required_fields = ['version', 'feedUri', 'timestamp', 'hash', 'latestChunkUri', 'latestChunkHash']
    for field in required_fields:
        if field not in wellknown_data:
            print(f"❌ Well-known file missing required field: {field}")
            return False
    
    if wellknown_data['version'] != '2.0':
        print(f"❌ Expected version 2.0, got {wellknown_data['version']}")
        return False
    
    print("✓ Basic pagination passed")
    return True


def test_blockchain_structure():
    """Test that chunks form a valid blockchain."""
    print("\nTesting blockchain structure...")
    
    test_dir = Path("paginated-examples")
    
    # Load tech-agents chunks
    chunk_files = sorted([
        f for f in test_dir.glob("tech-agents-*.json")
    ])
    
    if len(chunk_files) < 2:
        print(f"❌ Not enough chunks to test blockchain structure")
        return False
    
    chunks = []
    for chunk_file in chunk_files:
        with open(chunk_file, 'r') as f:
            chunks.append(json.load(f))
    
    # Verify blockchain links
    for i in range(1, len(chunks)):
        current_chunk = chunks[i]
        previous_chunk = chunks[i - 1]
        
        # Check that current chunk references previous chunk
        if 'previousHash' not in current_chunk:
            print(f"❌ Chunk {i} missing previousHash")
            return False
        
        if current_chunk['previousHash'] != previous_chunk['hash']:
            print(f"❌ Chunk {i} previousHash doesn't match previous chunk hash")
            print(f"  Expected: {previous_chunk['hash']}")
            print(f"  Got: {current_chunk['previousHash']}")
            return False
    
    print("✓ Blockchain structure valid")
    return True


def test_chunk_integrity():
    """Test that chunk hashes are valid."""
    print("\nTesting chunk integrity...")
    
    from pagination_manager import compute_chunk_hash, verify_chunk_chain
    
    test_dir = Path("paginated-examples")
    
    # Load tech-agents chunks
    chunk_files = sorted([
        f for f in test_dir.glob("tech-agents-*.json")
    ])
    
    chunks = []
    for chunk_file in chunk_files:
        with open(chunk_file, 'r') as f:
            chunks.append(json.load(f))
    
    # Verify each chunk's hash
    for i, chunk in enumerate(chunks):
        computed_hash = compute_chunk_hash(chunk, exclude_hash=True)
        if computed_hash != chunk['hash']:
            print(f"❌ Chunk {i} hash mismatch")
            print(f"  Expected: {chunk['hash']}")
            print(f"  Computed: {computed_hash}")
            return False
    
    # Verify the entire chain
    if not verify_chunk_chain(chunks):
        print(f"❌ Chain verification failed")
        return False
    
    print("✓ Chunk integrity verified")
    return True


def test_wellknown_structure():
    """Test well-known feed structure."""
    print("\nTesting well-known feed structure...")
    
    test_dir = Path("paginated-examples")
    wellknown_file = test_dir / "tech-agents.json"
    
    if not wellknown_file.exists():
        print(f"❌ Well-known file doesn't exist")
        return False
    
    with open(wellknown_file, 'r') as f:
        wellknown = json.load(f)
    
    # Verify structure
    required_fields = ['version', 'feedUri', 'timestamp', 'hash', 'latestChunkUri', 'latestChunkHash', 'pageSize']
    for field in required_fields:
        if field not in wellknown:
            print(f"❌ Well-known file missing required field: {field}")
            return False
    
    # Load the latest chunk
    latest_chunk_name = Path(wellknown['latestChunkUri']).name
    latest_chunk_file = test_dir / latest_chunk_name
    
    if not latest_chunk_file.exists():
        print(f"❌ Latest chunk file doesn't exist: {latest_chunk_name}")
        return False
    
    with open(latest_chunk_file, 'r') as f:
        latest_chunk = json.load(f)
    
    # Verify hash matches
    if latest_chunk['hash'] != wellknown['latestChunkHash']:
        print(f"❌ Latest chunk hash mismatch")
        print(f"  Well-known says: {wellknown['latestChunkHash']}")
        print(f"  Chunk has: {latest_chunk['hash']}")
        return False
    
    print("✓ Well-known structure valid")
    return True


def test_page_size():
    """Test that page size is respected."""
    print("\nTesting page size...")
    
    test_dir = Path("paginated-examples")
    
    # Load tech-agents chunks (page size 2)
    chunk_files = sorted([
        f for f in test_dir.glob("tech-agents-*.json")
    ])
    
    for chunk_file in chunk_files:
        with open(chunk_file, 'r') as f:
            chunk = json.load(f)
        
        if 'posts' in chunk:
            if len(chunk['posts']) > 2:
                print(f"❌ Chunk has more posts than page size: {len(chunk['posts'])} > 2")
                return False
    
    print("✓ Page size respected")
    return True


def test_main_feed_pagination():
    """Test main feed pagination."""
    print("\nTesting main feed pagination...")
    
    test_dir = Path("paginated-examples")
    
    # Load main feed chunks
    chunk_files = sorted([
        f for f in test_dir.glob("main-*.json")
    ])
    
    if len(chunk_files) < 2:
        print(f"❌ Not enough main feed chunks")
        return False
    
    chunks = []
    for chunk_file in chunk_files:
        with open(chunk_file, 'r') as f:
            chunks.append(json.load(f))
    
    # Verify structure
    for chunk in chunks:
        if 'submolts' not in chunk:
            print(f"❌ Main feed chunk missing submolts")
            return False
    
    # Sort chunks by blockchain: find the root (no previousHash), then follow the chain
    root_chunk = None
    chunk_map = {}
    
    for chunk in chunks:
        chunk_map[chunk['hash']] = chunk
        if 'previousHash' not in chunk:
            if root_chunk is not None:
                print(f"❌ Multiple root chunks found")
                return False
            root_chunk = chunk
    
    if root_chunk is None:
        print(f"❌ No root chunk found")
        return False
    
    # Build ordered chain
    ordered_chunks = [root_chunk]
    for chunk in chunks:
        if chunk['hash'] == root_chunk['hash']:
            continue
        if 'previousHash' in chunk and chunk['previousHash'] == root_chunk['hash']:
            ordered_chunks.append(chunk)
            break
    
    # Verify blockchain links
    for i in range(1, len(ordered_chunks)):
        if 'previousHash' not in ordered_chunks[i]:
            print(f"❌ Main feed chunk {i} missing previousHash")
            return False
        if ordered_chunks[i]['previousHash'] != ordered_chunks[i - 1]['hash']:
            print(f"❌ Main feed blockchain broken at chunk {i}")
            return False
    
    print("✓ Main feed pagination valid")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Moltbook Pagination System Tests")
    print("=" * 60)
    
    all_passed = True
    
    # Run tests
    if not test_pagination_basic():
        all_passed = False
    
    if not test_blockchain_structure():
        all_passed = False
    
    if not test_chunk_integrity():
        all_passed = False
    
    if not test_wellknown_structure():
        all_passed = False
    
    if not test_page_size():
        all_passed = False
    
    if not test_main_feed_pagination():
        all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All pagination tests passed!")
        print("=" * 60)
        return 0
    else:
        print("❌ Some pagination tests failed!")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
