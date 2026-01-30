#!/usr/bin/env python3
"""
Example Moltbook Feed Consumer

Demonstrates how to consume paginated Moltbook feeds with blockchain verification.
"""

import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime


def compute_hash(data: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def compute_chunk_hash(chunk: Dict[str, Any]) -> str:
    """Compute hash for a feed chunk."""
    parts = [
        chunk.get('version', '2.0'),
        chunk['feedUri'],
        chunk['timestamp'],
    ]
    
    if 'previousHash' in chunk:
        parts.append(chunk['previousHash'])
    
    if 'submolts' in chunk:
        submolt_data = '|'.join(s['id'] + ':' + s['hash'] for s in chunk['submolts'])
        parts.append(submolt_data)
    elif 'posts' in chunk:
        post_data = '|'.join(p['id'] + ':' + p['hash'] for p in chunk['posts'])
        parts.append(post_data)
    
    canonical_data = '|'.join(parts)
    return compute_hash(canonical_data)


class MoltbookFeedConsumer:
    """Consumer for Moltbook paginated feeds."""
    
    def __init__(self, base_url: str = "https://www.moltbook.com/feeds/"):
        self.base_url = base_url
        self.cache = {}  # Simple in-memory cache
    
    def fetch_json(self, url: str) -> Dict[str, Any]:
        """
        Fetch JSON from URL. In real implementation, use requests library.
        For this example, we'll read from local files.
        """
        # Convert URL to local file path for demo
        filename = url.replace(self.base_url, '')
        try:
            with open(f"paginated-examples/{filename}", 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Try without paginated-examples prefix
            try:
                with open(filename, 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                raise Exception(f"File not found: {filename}")
    
    def verify_chunk_hash(self, chunk: Dict[str, Any]) -> bool:
        """Verify a chunk's hash."""
        computed = compute_chunk_hash(chunk)
        return computed == chunk['hash']
    
    def fetch_wellknown(self, feed_name: str) -> Dict[str, Any]:
        """Fetch a well-known feed."""
        url = f"{self.base_url}{feed_name}.json"
        wellknown = self.fetch_json(url)
        
        print(f"📡 Fetched well-known feed: {feed_name}.json")
        print(f"   Latest chunk: {wellknown['latestChunkUri'].split('/')[-1]}")
        print(f"   Page size: {wellknown['pageSize']}")
        
        return wellknown
    
    def fetch_latest_chunk(self, wellknown: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch the latest chunk from a well-known feed."""
        latest_uri = wellknown['latestChunkUri']
        
        # Check cache
        if latest_uri in self.cache:
            print(f"💾 Using cached chunk: {latest_uri.split('/')[-1]}")
            return self.cache[latest_uri]
        
        # Fetch from network
        chunk = self.fetch_json(latest_uri)
        
        # Verify hash
        if not self.verify_chunk_hash(chunk):
            raise Exception("Chunk hash verification failed!")
        
        # Verify against well-known hash
        if chunk['hash'] != wellknown['latestChunkHash']:
            raise Exception("Latest chunk hash doesn't match well-known!")
        
        # Cache it
        self.cache[latest_uri] = chunk
        
        print(f"✅ Fetched and verified latest chunk: {latest_uri.split('/')[-1]}")
        return chunk
    
    def fetch_history(
        self,
        start_chunk: Dict[str, Any],
        max_chunks: int = 10
    ) -> List[Dict[str, Any]]:
        """Fetch historical chunks following the blockchain."""
        chunks = [start_chunk]
        current = start_chunk
        
        while 'previousUri' in current and len(chunks) < max_chunks:
            prev_uri = current['previousUri']
            
            # Check cache
            if prev_uri in self.cache:
                print(f"💾 Using cached chunk: {prev_uri.split('/')[-1]}")
                prev_chunk = self.cache[prev_uri]
            else:
                # Fetch from network
                prev_chunk = self.fetch_json(prev_uri)
                
                # Verify hash
                if not self.verify_chunk_hash(prev_chunk):
                    raise Exception(f"Chunk hash verification failed for {prev_uri}")
                
                # Verify blockchain link
                if prev_chunk['hash'] != current['previousHash']:
                    raise Exception("Blockchain verification failed!")
                
                # Cache it
                self.cache[prev_uri] = prev_chunk
                
                print(f"✅ Fetched and verified chunk: {prev_uri.split('/')[-1]}")
            
            chunks.append(prev_chunk)
            current = prev_chunk
        
        return chunks
    
    def check_for_updates(
        self,
        feed_name: str,
        last_known_hash: Optional[str] = None
    ) -> bool:
        """Check if there are updates to a feed."""
        wellknown = self.fetch_wellknown(feed_name)
        
        if last_known_hash is None:
            return True  # First fetch
        
        if wellknown['latestChunkHash'] != last_known_hash:
            print(f"🔔 New content available in {feed_name}!")
            return True
        
        print(f"✓ No updates for {feed_name}")
        return False
    
    def display_posts(self, chunks: List[Dict[str, Any]]) -> None:
        """Display posts from chunks."""
        print("\n" + "=" * 60)
        print("POSTS")
        print("=" * 60)
        
        for chunk in reversed(chunks):  # Oldest first
            if 'posts' not in chunk:
                continue
            
            for post in chunk['posts']:
                print(f"\n[@{post['author']}] {post['timestamp']}")
                print(f"{post['content']}")
                
                if post.get('comments'):
                    print(f"  💬 {len(post['comments'])} comment(s)")
                    for comment in post['comments'][:2]:  # Show first 2
                        print(f"    └─ @{comment['author']}: {comment['content'][:50]}...")


def main():
    """Example usage of the feed consumer."""
    print("=" * 60)
    print("Moltbook Feed Consumer Example")
    print("=" * 60)
    print()
    
    # Create consumer
    consumer = MoltbookFeedConsumer()
    
    # Fetch main feed
    print("1️⃣ Fetching main feed...")
    main_wellknown = consumer.fetch_wellknown('main')
    main_latest = consumer.fetch_latest_chunk(main_wellknown)
    
    print(f"\n   Found {len(main_latest.get('submolts', []))} submolt(s) in latest chunk")
    for submolt in main_latest.get('submolts', []):
        print(f"   - {submolt['title']} ({submolt['id']})")
    
    # Fetch history
    if 'previousUri' in main_latest:
        print(f"\n2️⃣ Fetching main feed history...")
        main_history = consumer.fetch_history(main_latest, max_chunks=5)
        print(f"\n   Total chunks in history: {len(main_history)}")
    
    # Fetch a submolt feed
    print(f"\n3️⃣ Fetching submolt feed: tech-agents...")
    submolt_wellknown = consumer.fetch_wellknown('tech-agents')
    submolt_latest = consumer.fetch_latest_chunk(submolt_wellknown)
    
    print(f"\n   Found {len(submolt_latest.get('posts', []))} post(s) in latest chunk")
    
    # Fetch submolt history
    if 'previousUri' in submolt_latest:
        print(f"\n4️⃣ Fetching submolt history...")
        submolt_history = consumer.fetch_history(submolt_latest, max_chunks=5)
        print(f"\n   Total chunks in history: {len(submolt_history)}")
        
        # Display posts
        consumer.display_posts(submolt_history)
    
    # Simulate checking for updates
    print(f"\n5️⃣ Checking for updates...")
    has_updates = consumer.check_for_updates(
        'tech-agents',
        last_known_hash=submolt_wellknown['latestChunkHash']
    )
    
    print("\n" + "=" * 60)
    print("✅ Example complete!")
    print("=" * 60)
    print(f"\nCache stats:")
    print(f"  Cached chunks: {len(consumer.cache)}")
    print(f"  Cache size: ~{sum(len(json.dumps(c)) for c in consumer.cache.values())} bytes")


if __name__ == '__main__':
    main()
