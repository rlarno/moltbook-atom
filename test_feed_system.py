#!/usr/bin/env python3
"""
Test script for Moltbook feed system.
Validates all components and examples.
"""

import json
import sys
import subprocess
from pathlib import Path


def run_command(cmd):
    """Run a shell command and return output."""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def test_integrity_checker():
    """Test the integrity checker utility."""
    print("Testing integrity checker...")
    
    # Test main feed verification
    code, stdout, stderr = run_command(
        "python integrity_checker.py example-main-feed.json --verify"
    )
    if code != 0:
        print(f"❌ Main feed verification failed!")
        print(f"STDERR: {stderr}")
        return False
    
    result = json.loads(stdout)
    if not result['valid']:
        print(f"❌ Main feed integrity check failed!")
        return False
    
    print("✓ Main feed verification passed")
    
    # Test submolt feed verification
    code, stdout, stderr = run_command(
        "python integrity_checker.py example-submolt-feed.json --verify"
    )
    if code != 0:
        print(f"❌ Submolt feed verification failed!")
        print(f"STDERR: {stderr}")
        return False
    
    result = json.loads(stdout)
    if not result['valid']:
        print(f"❌ Submolt feed integrity check failed!")
        return False
    
    print("✓ Submolt feed verification passed")
    
    return True


def test_feed_generator():
    """Test the feed generator utility."""
    print("\nTesting feed generator...")
    
    # Test post generation
    code, stdout, stderr = run_command(
        'python feed_generator.py post "test-001" "test-agent" "Test content"'
    )
    if code != 0:
        print(f"❌ Post generation failed!")
        print(f"STDERR: {stderr}")
        return False
    
    try:
        post = json.loads(stdout)
        if 'hash' not in post or not post['hash']:
            print(f"❌ Generated post missing hash!")
            return False
        print("✓ Post generation passed")
    except json.JSONDecodeError:
        print(f"❌ Post generation produced invalid JSON!")
        return False
    
    # Test comment generation
    code, stdout, stderr = run_command(
        'python feed_generator.py comment "test-comment-001" "test-agent" "Test comment"'
    )
    if code != 0:
        print(f"❌ Comment generation failed!")
        print(f"STDERR: {stderr}")
        return False
    
    print("✓ Comment generation passed")
    
    # Test submolt generation
    code, stdout, stderr = run_command(
        'python feed_generator.py submolt "test" "Test" "Test submolt" "https://test.com/feed.json"'
    )
    if code != 0:
        print(f"❌ Submolt generation failed!")
        print(f"STDERR: {stderr}")
        return False
    
    try:
        submolt = json.loads(stdout)
        if 'hash' not in submolt or not submolt['hash']:
            print(f"❌ Generated submolt missing hash!")
            return False
        print("✓ Submolt generation passed")
    except json.JSONDecodeError:
        print(f"❌ Submolt generation produced invalid JSON!")
        return False
    
    # Test feed generation
    code, stdout, stderr = run_command(
        'python feed_generator.py feed "https://test.com/main.json" "Test Feed" "Test Description"'
    )
    if code != 0:
        print(f"❌ Feed generation failed!")
        print(f"STDERR: {stderr}")
        return False
    
    try:
        feed = json.loads(stdout)
        if 'hash' not in feed or not feed['hash']:
            print(f"❌ Generated feed missing hash!")
            return False
        print("✓ Feed generation passed")
    except json.JSONDecodeError:
        print(f"❌ Feed generation produced invalid JSON!")
        return False
    
    return True


def test_example_files():
    """Test that example files are valid JSON and have correct structure."""
    print("\nTesting example files...")
    
    # Test main feed structure
    with open('example-main-feed.json', 'r') as f:
        main_feed = json.load(f)
    
    required_fields = ['version', 'feedUri', 'timestamp', 'hash', 'submolts']
    for field in required_fields:
        if field not in main_feed:
            print(f"❌ Main feed missing required field: {field}")
            return False
    
    print("✓ Main feed structure valid")
    
    # Test submolt feed structure
    with open('example-submolt-feed.json', 'r') as f:
        submolt_feed = json.load(f)
    
    required_fields = ['id', 'title', 'uri', 'hash', 'posts']
    for field in required_fields:
        if field not in submolt_feed:
            print(f"❌ Submolt feed missing required field: {field}")
            return False
    
    # Check posts structure
    if len(submolt_feed['posts']) > 0:
        post = submolt_feed['posts'][0]
        required_fields = ['id', 'author', 'content', 'timestamp', 'hash']
        for field in required_fields:
            if field not in post:
                print(f"❌ Post missing required field: {field}")
                return False
    
    print("✓ Submolt feed structure valid")
    
    return True


def test_hash_regeneration():
    """Test hash regeneration."""
    print("\nTesting hash regeneration...")
    
    # Test adding hashes to main feed
    code, stdout, stderr = run_command(
        "python integrity_checker.py example-main-feed.json --add-hashes"
    )
    if code != 0:
        print(f"❌ Hash regeneration for main feed failed!")
        print(f"STDERR: {stderr}")
        return False
    
    try:
        feed = json.loads(stdout)
        if 'hash' not in feed:
            print(f"❌ Regenerated main feed missing hash!")
            return False
    except json.JSONDecodeError:
        print(f"❌ Hash regeneration produced invalid JSON!")
        return False
    
    print("✓ Main feed hash regeneration passed")
    
    # Test adding hashes to submolt feed
    code, stdout, stderr = run_command(
        "python integrity_checker.py example-submolt-feed.json --add-hashes"
    )
    if code != 0:
        print(f"❌ Hash regeneration for submolt feed failed!")
        print(f"STDERR: {stderr}")
        return False
    
    try:
        submolt = json.loads(stdout)
        if 'hash' not in submolt:
            print(f"❌ Regenerated submolt missing hash!")
            return False
    except json.JSONDecodeError:
        print(f"❌ Hash regeneration produced invalid JSON!")
        return False
    
    print("✓ Submolt feed hash regeneration passed")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Moltbook Feed System Tests")
    print("=" * 60)
    
    all_passed = True
    
    # Run tests
    if not test_example_files():
        all_passed = False
    
    if not test_integrity_checker():
        all_passed = False
    
    if not test_feed_generator():
        all_passed = False
    
    if not test_hash_regeneration():
        all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed!")
        print("=" * 60)
        return 0
    else:
        print("❌ Some tests failed!")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
