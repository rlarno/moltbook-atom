#!/usr/bin/env python3
"""
Moltbook Feed Integrity Checker

Utility for generating and verifying SHA-256 hashes for Moltbook feed content.
Ensures data integrity for posts, comments, submolts, and entire feeds.
"""

import json
import hashlib
from typing import Dict, Any, List
from datetime import datetime


def compute_hash(data: str) -> str:
    """
    Compute SHA-256 hash of a string.
    
    Args:
        data: String data to hash
        
    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def compute_post_hash(post: Dict[str, Any]) -> str:
    """
    Compute hash for a post (excluding the hash field itself).
    
    Args:
        post: Post dictionary
        
    Returns:
        SHA-256 hash of post content
    """
    # Create a canonical representation excluding hash and comments
    canonical_data = f"{post['id']}|{post['author']}|{post['content']}|{post['timestamp']}"
    return compute_hash(canonical_data)


def compute_comment_hash(comment: Dict[str, Any]) -> str:
    """
    Compute hash for a comment (excluding the hash field itself).
    
    Args:
        comment: Comment dictionary
        
    Returns:
        SHA-256 hash of comment content
    """
    canonical_data = f"{comment['id']}|{comment['author']}|{comment['content']}|{comment['timestamp']}"
    return compute_hash(canonical_data)


def compute_submolt_hash(submolt: Dict[str, Any]) -> str:
    """
    Compute hash for a submolt (excluding the hash field and posts).
    
    Args:
        submolt: Submolt dictionary
        
    Returns:
        SHA-256 hash of submolt metadata
    """
    canonical_data = f"{submolt['id']}|{submolt['title']}|{submolt.get('description', '')}|{submolt['uri']}"
    return compute_hash(canonical_data)


def compute_feed_hash(feed: Dict[str, Any]) -> str:
    """
    Compute hash for the entire feed (excluding the hash field itself).
    
    Args:
        feed: Feed dictionary
        
    Returns:
        SHA-256 hash of feed content
    """
    # Include version, feedUri, and all submolt hashes
    submolt_hashes = '|'.join(s['hash'] for s in feed['submolts'])
    canonical_data = f"{feed['version']}|{feed['feedUri']}|{feed['timestamp']}|{submolt_hashes}"
    return compute_hash(canonical_data)


def add_hashes_to_post(post: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add hashes to a post and all its comments.
    
    Args:
        post: Post dictionary
        
    Returns:
        Post with computed hashes
    """
    # Add hashes to comments first
    if 'comments' in post:
        for comment in post['comments']:
            comment['hash'] = compute_comment_hash(comment)
    
    # Add hash to post
    post['hash'] = compute_post_hash(post)
    return post


def add_hashes_to_submolt(submolt: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add hashes to a submolt and all its posts.
    
    Args:
        submolt: Submolt dictionary
        
    Returns:
        Submolt with computed hashes
    """
    # Add hashes to all posts
    if 'posts' in submolt:
        for post in submolt['posts']:
            add_hashes_to_post(post)
    
    # Add hash to submolt
    submolt['hash'] = compute_submolt_hash(submolt)
    return submolt


def add_hashes_to_feed(feed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add hashes to the entire feed structure.
    
    Args:
        feed: Feed dictionary
        
    Returns:
        Feed with all computed hashes
    """
    # Add hashes to all submolts
    for submolt in feed['submolts']:
        add_hashes_to_submolt(submolt)
    
    # Add hash to feed
    feed['hash'] = compute_feed_hash(feed)
    return feed


def verify_post_hash(post: Dict[str, Any]) -> bool:
    """
    Verify the hash of a post.
    
    Args:
        post: Post dictionary with hash
        
    Returns:
        True if hash is valid, False otherwise
    """
    expected_hash = compute_post_hash(post)
    return post.get('hash') == expected_hash


def verify_comment_hash(comment: Dict[str, Any]) -> bool:
    """
    Verify the hash of a comment.
    
    Args:
        comment: Comment dictionary with hash
        
    Returns:
        True if hash is valid, False otherwise
    """
    expected_hash = compute_comment_hash(comment)
    return comment.get('hash') == expected_hash


def verify_submolt_hash(submolt: Dict[str, Any]) -> bool:
    """
    Verify the hash of a submolt.
    
    Args:
        submolt: Submolt dictionary with hash
        
    Returns:
        True if hash is valid, False otherwise
    """
    expected_hash = compute_submolt_hash(submolt)
    return submolt.get('hash') == expected_hash


def verify_feed_hash(feed: Dict[str, Any]) -> bool:
    """
    Verify the hash of the entire feed.
    
    Args:
        feed: Feed dictionary with hash
        
    Returns:
        True if hash is valid, False otherwise
    """
    expected_hash = compute_feed_hash(feed)
    return feed.get('hash') == expected_hash


def verify_feed_integrity(feed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify integrity of entire feed structure.
    
    Args:
        feed: Feed dictionary
        
    Returns:
        Dictionary with verification results
    """
    results = {
        'valid': True,
        'feed_hash_valid': verify_feed_hash(feed),
        'submolts': []
    }
    
    if not results['feed_hash_valid']:
        results['valid'] = False
    
    for submolt in feed['submolts']:
        submolt_result = {
            'id': submolt['id'],
            'submolt_hash_valid': verify_submolt_hash(submolt),
            'posts': []
        }
        
        if not submolt_result['submolt_hash_valid']:
            results['valid'] = False
        
        if 'posts' in submolt:
            for post in submolt['posts']:
                post_result = {
                    'id': post['id'],
                    'post_hash_valid': verify_post_hash(post),
                    'comments': []
                }
                
                if not post_result['post_hash_valid']:
                    results['valid'] = False
                
                if 'comments' in post:
                    for comment in post['comments']:
                        comment_valid = verify_comment_hash(comment)
                        post_result['comments'].append({
                            'id': comment['id'],
                            'comment_hash_valid': comment_valid
                        })
                        
                        if not comment_valid:
                            results['valid'] = False
                
                submolt_result['posts'].append(post_result)
        
        results['submolts'].append(submolt_result)
    
    return results


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python integrity_checker.py <feed.json> [--verify (default)|--add-hashes] [--type main|submolt]")
        sys.exit(1)
    
    feed_file = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else '--verify'
    feed_type = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Auto-detect feed type if not specified
    if feed_type is None:
        with open(feed_file, 'r') as f:
            feed_data = json.load(f)
        if 'submolts' in feed_data:
            feed_type = 'main'
        else:
            feed_type = 'submolt'
    else:
        with open(feed_file, 'r') as f:
            feed_data = json.load(f)
    
    if mode == '--add-hashes':
        # Add hashes based on feed type
        if feed_type == 'main':
            feed_data = add_hashes_to_feed(feed_data)
        else:
            feed_data = add_hashes_to_submolt(feed_data)
        print(json.dumps(feed_data, indent=2))
    else:
        # Verify feed integrity
        if feed_type == 'main':
            results = verify_feed_integrity(feed_data)
            print(json.dumps(results, indent=2))
            sys.exit(0 if results['valid'] else 1)
        else:
            # Verify submolt
            submolt_valid = verify_submolt_hash(feed_data)
            posts_valid = True
            post_results = []
            
            if 'posts' in feed_data:
                for post in feed_data['posts']:
                    post_valid = verify_post_hash(post)
                    if not post_valid:
                        posts_valid = False
                    
                    comment_results = []
                    if 'comments' in post:
                        for comment in post['comments']:
                            comment_valid = verify_comment_hash(comment)
                            if not comment_valid:
                                posts_valid = False
                            comment_results.append({
                                'id': comment['id'],
                                'valid': comment_valid
                            })
                    
                    post_results.append({
                        'id': post['id'],
                        'valid': post_valid,
                        'comments': comment_results
                    })
            
            results = {
                'valid': submolt_valid and posts_valid,
                'submolt_hash_valid': submolt_valid,
                'posts': post_results
            }
            print(json.dumps(results, indent=2))
            sys.exit(0 if results['valid'] else 1)
