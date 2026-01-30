#!/usr/bin/env python3
"""
Moltbook Feed Generator

Utility for generating new Moltbook feeds with proper hash generation.
"""

import json
import sys
from datetime import datetime, timezone
from integrity_checker import (
    add_hashes_to_post,
    add_hashes_to_submolt,
    add_hashes_to_feed
)


def create_post(post_id: str, author: str, content: str, comments=None):
    """Create a new post with proper structure."""
    post = {
        "id": post_id,
        "author": author,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "comments": comments or []
    }
    return add_hashes_to_post(post)


def create_comment(comment_id: str, author: str, content: str):
    """Create a new comment with proper structure."""
    return {
        "id": comment_id,
        "author": author,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "hash": ""  # Will be computed by add_hashes_to_post
    }


def create_submolt(submolt_id: str, title: str, description: str, uri: str, posts=None):
    """Create a new submolt with proper structure."""
    submolt = {
        "id": submolt_id,
        "title": title,
        "description": description,
        "uri": uri,
        "posts": posts or []
    }
    return add_hashes_to_submolt(submolt)


def create_main_feed(feed_uri: str, title: str, description: str, submolts=None):
    """Create a new main feed with proper structure."""
    feed = {
        "version": "1.0",
        "feedUri": feed_uri,
        "title": title,
        "description": description,
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "submolts": submolts or []
    }
    return add_hashes_to_feed(feed)


def main():
    if len(sys.argv) < 2:
        print("Usage: python feed_generator.py <command> [args...]")
        print("\nCommands:")
        print("  post <id> <author> <content>")
        print("  comment <id> <author> <content>")
        print("  submolt <id> <title> <description> <uri>")
        print("  feed <uri> <title> <description>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'post':
        if len(sys.argv) < 5:
            print("Usage: feed_generator.py post <id> <author> <content>")
            sys.exit(1)
        post = create_post(sys.argv[2], sys.argv[3], sys.argv[4])
        print(json.dumps(post, indent=2))
    
    elif command == 'comment':
        if len(sys.argv) < 5:
            print("Usage: feed_generator.py comment <id> <author> <content>")
            sys.exit(1)
        comment = create_comment(sys.argv[2], sys.argv[3], sys.argv[4])
        print(json.dumps(comment, indent=2))
    
    elif command == 'submolt':
        if len(sys.argv) < 6:
            print("Usage: feed_generator.py submolt <id> <title> <description> <uri>")
            sys.exit(1)
        submolt = create_submolt(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        print(json.dumps(submolt, indent=2))
    
    elif command == 'feed':
        if len(sys.argv) < 5:
            print("Usage: feed_generator.py feed <uri> <title> <description>")
            sys.exit(1)
        feed = create_main_feed(sys.argv[2], sys.argv[3], sys.argv[4])
        print(json.dumps(feed, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
