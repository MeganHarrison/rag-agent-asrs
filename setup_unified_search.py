#!/usr/bin/env python3
"""Setup unified search functions for all FM Global tables."""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def setup_unified_search():
    """Create unified search functions."""
    
    db_url = os.getenv('DATABASE_URL')
    
    try:
        conn = await asyncpg.connect(db_url)
        print("✅ Connected to database")
        
        # Read SQL file
        with open('sql/create_unified_search.sql', 'r') as f:
            sql = f.read()
        
        # Execute SQL
        await conn.execute(sql)
        print("✅ Unified search functions created successfully")
        
        # Test the search function
        print("\n📊 Testing unified search...")
        
        # Create a test embedding (normally you'd use OpenAI)
        test_embedding = [0.1] * 1536  # Dummy embedding
        
        results = await conn.fetch("""
            SELECT source_table, source_type, title, similarity
            FROM search_fm_global_all($1::vector, $2, 5)
        """, test_embedding, "fire protection")
        
        print(f"Found {len(results)} results:")
        for r in results:
            print(f"  - {r['source_table']}: {r['title'][:50]}... (similarity: {r['similarity']:.3f})")
        
        # Test text search
        print("\n📊 Testing text search...")
        text_results = await conn.fetch("""
            SELECT doc_id, chunk_summary
            FROM text_search_chunks($1, 3)
        """, "sprinkler")
        
        print(f"Found {len(text_results)} text matches:")
        for r in text_results:
            summary = r['chunk_summary'][:100] if r['chunk_summary'] else 'No summary'
            print(f"  - {r['doc_id']}: {summary}...")
        
        await conn.close()
        print("\n✅ Setup complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(setup_unified_search())