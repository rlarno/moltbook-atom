#!/usr/bin/env python3
"""
Moltbook Feed Pagination Manager

Utility for managing blockchain-like paginated feeds with integrity checking.
Each feed chunk points to the previous chunk, similar to a blockchain structure.
"""

import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from pathlib import Path

# Optimal page size: 50 items
# This balances performance (small enough for fast loading) with overhead (not too many chunks)
# At ~2KB per post with comments, 50 posts = ~100KB per chunk
DEFAULT_PAGE_SIZE = 50


def compute_hash(data: str) -> str:
    """
    Compute SHA-256 hash of a string.
    
    Args:
        data: String data to hash
        
    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def generate_chunk_filename(base_name: str, timestamp: datetime, content_hash: str) -> str:
    """
    Generate a filename for a feed chunk based on timestamp and content hash.
    
    Args:
        base_name: Base name (e.g., 'main' or 'tech-agents')
        timestamp: Timestamp for the chunk
        content_hash: Hash of the chunk content (first 8 chars for brevity)
        
    Returns:
        Filename in format: base-yyyy-mm-dd-hhmmss-hash.json
    """
    date_str = timestamp.strftime('%Y-%m-%d-%H%M%S')
    hash_short = content_hash[:8]
    return f"{base_name}-{date_str}-{hash_short}.json"


def compute_chunk_hash(chunk: Dict[str, Any], exclude_hash: bool = True) -> str:
    """
    Compute hash for a feed chunk.
    
    Args:
        chunk: Chunk dictionary
        exclude_hash: Whether to exclude the hash field itself from computation
        
    Returns:
        SHA-256 hash of chunk content
    """
    # Create canonical representation
    parts = [
        chunk.get('version', '2.0'),
        chunk['feedUri'],
        chunk['timestamp'],
    ]
    
    # Add previous hash if present (blockchain link)
    if 'previousHash' in chunk:
        parts.append(chunk['previousHash'])
    
    # Add content based on chunk type
    if 'submolts' in chunk:
        # Main feed chunk
        submolt_data = '|'.join(s['id'] + ':' + s['hash'] for s in chunk['submolts'])
        parts.append(submolt_data)
    elif 'posts' in chunk:
        # Submolt feed chunk
        post_data = '|'.join(p['id'] + ':' + p['hash'] for p in chunk['posts'])
        parts.append(post_data)
    
    canonical_data = '|'.join(parts)
    return compute_hash(canonical_data)


def split_feed_into_chunks(
    feed: Dict[str, Any],
    base_name: str,
    page_size: int = DEFAULT_PAGE_SIZE,
    base_uri: str = "https://www.moltbook.com/feeds/"
) -> List[Dict[str, Any]]:
    """
    Split a feed into paginated chunks with blockchain-like structure.
    
    Args:
        feed: Complete feed dictionary
        base_name: Base name for chunk files (e.g., 'main' or 'submolt-id')
        page_size: Number of items per chunk
        base_uri: Base URI for feed files
        
    Returns:
        List of chunk dictionaries, ordered from oldest to newest
    """
    chunks = []
    
    # Get the feed URI (could be 'feedUri' or 'uri')
    feed_uri = feed.get('feedUri') or feed.get('uri', f"{base_uri}{base_name}.json")
    
    # Determine what to paginate
    if 'submolts' in feed:
        # Main feed - paginate submolts
        items = feed['submolts']
        item_key = 'submolts'
    elif 'posts' in feed:
        # Submolt feed - paginate posts
        items = feed['posts']
        item_key = 'posts'
    else:
        # No items to paginate
        return [feed]
    
    if len(items) == 0:
        # Empty feed
        return [feed]
    
    # Split items into pages
    num_chunks = (len(items) + page_size - 1) // page_size
    
    for i in range(num_chunks):
        start_idx = i * page_size
        end_idx = min((i + 1) * page_size, len(items))
        chunk_items = items[start_idx:end_idx]
        
        # Get timestamp from the latest item in this chunk
        if item_key == 'posts':
            chunk_timestamp = chunk_items[-1]['timestamp']
        else:
            chunk_timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        # Create chunk
        chunk = {
            'version': '2.0',
            'feedUri': feed_uri,
            'timestamp': chunk_timestamp,
            'pageSize': page_size,
            item_key: chunk_items
        }
        
        # Add optional metadata
        if 'title' in feed:
            chunk['title'] = feed['title']
        if 'description' in feed:
            chunk['description'] = feed['description']
        if 'id' in feed:
            chunk['id'] = feed['id']
        
        # Add blockchain link to previous chunk
        if i > 0:
            prev_chunk = chunks[i - 1]
            prev_hash = prev_chunk['hash']
            prev_filename = prev_chunk['_filename']
            
            chunk['previousUri'] = f"{base_uri}{prev_filename}"
            chunk['previousHash'] = prev_hash
        
        # Compute hash for this chunk
        chunk['hash'] = compute_chunk_hash(chunk, exclude_hash=True)
        
        # Generate filename
        ts = datetime.fromisoformat(chunk_timestamp.replace('Z', '+00:00'))
        chunk['_filename'] = generate_chunk_filename(base_name, ts, chunk['hash'])
        
        chunks.append(chunk)
    
    return chunks


def create_wellknown_feed(
    latest_chunk: Dict[str, Any],
    wellknown_uri: str
) -> Dict[str, Any]:
    """
    Create the well-known feed file that points to the latest chunk.
    
    Args:
        latest_chunk: The most recent chunk
        wellknown_uri: URI for the well-known feed (e.g., main.json)
        
    Returns:
        Well-known feed dictionary
    """
    wellknown = {
        'version': '2.0',
        'feedUri': wellknown_uri,
        'timestamp': latest_chunk['timestamp'],
        'latestChunkUri': latest_chunk['feedUri'],
        'latestChunkHash': latest_chunk['hash'],
        'pageSize': latest_chunk.get('pageSize', DEFAULT_PAGE_SIZE)
    }
    
    # Add optional metadata
    if 'title' in latest_chunk:
        wellknown['title'] = latest_chunk['title']
    if 'description' in latest_chunk:
        wellknown['description'] = latest_chunk['description']
    if 'id' in latest_chunk:
        wellknown['id'] = latest_chunk['id']
    
    # Compute hash for well-known feed
    canonical = f"{wellknown['version']}|{wellknown['feedUri']}|{wellknown['timestamp']}|{wellknown['latestChunkHash']}"
    wellknown['hash'] = compute_hash(canonical)
    
    return wellknown


def paginate_feed(
    feed: Dict[str, Any],
    base_name: str,
    output_dir: str = ".",
    base_uri: str = "https://www.moltbook.com/feeds/",
    page_size: int = DEFAULT_PAGE_SIZE
) -> Tuple[str, List[str]]:
    """
    Paginate a feed and write chunks to files.
    
    Args:
        feed: Complete feed dictionary
        base_name: Base name for files (e.g., 'main' or 'submolt-id')
        output_dir: Directory to write files to
        base_uri: Base URI for feed files
        page_size: Number of items per chunk
        
    Returns:
        Tuple of (wellknown_filename, list of chunk filenames)
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Split feed into chunks
    chunks = split_feed_into_chunks(feed, base_name, page_size, base_uri)
    
    # Write chunks to files
    chunk_files = []
    for chunk in chunks:
        filename = chunk['_filename']
        filepath = output_path / filename
        
        # Remove internal metadata
        chunk_to_save = {k: v for k, v in chunk.items() if not k.startswith('_')}
        
        with open(filepath, 'w') as f:
            json.dump(chunk_to_save, f, indent=2)
        
        chunk_files.append(filename)
    
    # Create well-known feed
    wellknown_filename = f"{base_name}.json"
    latest_chunk = chunks[-1]
    
    # Update latest chunk's feedUri to point to its actual file
    latest_chunk_copy = latest_chunk.copy()
    latest_chunk_copy['feedUri'] = f"{base_uri}{latest_chunk['_filename']}"
    
    wellknown = create_wellknown_feed(latest_chunk_copy, f"{base_uri}{wellknown_filename}")
    
    wellknown_path = output_path / wellknown_filename
    with open(wellknown_path, 'w') as f:
        json.dump(wellknown, f, indent=2)
    
    return wellknown_filename, chunk_files


def verify_chunk_chain(
    chunks: List[Dict[str, Any]]
) -> bool:
    """
    Verify the integrity of a chunk chain (blockchain verification).
    
    Args:
        chunks: List of chunks ordered from oldest to newest
        
    Returns:
        True if chain is valid, False otherwise
    """
    for i, chunk in enumerate(chunks):
        # Verify chunk hash
        computed_hash = compute_chunk_hash(chunk, exclude_hash=True)
        if computed_hash != chunk['hash']:
            return False
        
        # Verify blockchain link
        if i > 0:
            if 'previousHash' not in chunk:
                return False
            if chunk['previousHash'] != chunks[i - 1]['hash']:
                return False
    
    return True


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python pagination_manager.py <feed.json> <base_name> [output_dir] [page_size]")
        print("\nExample:")
        print("  python pagination_manager.py example-submolt-feed.json tech-agents ./paginated 50")
        sys.exit(1)
    
    feed_file = sys.argv[1]
    base_name = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "."
    page_size = int(sys.argv[4]) if len(sys.argv) > 4 else DEFAULT_PAGE_SIZE
    
    with open(feed_file, 'r') as f:
        feed = json.load(f)
    
    wellknown_file, chunk_files = paginate_feed(
        feed, base_name, output_dir, page_size=page_size
    )
    
    print(f"Created well-known feed: {wellknown_file}")
    print(f"Created {len(chunk_files)} chunk(s):")
    for chunk_file in chunk_files:
        print(f"  - {chunk_file}")
