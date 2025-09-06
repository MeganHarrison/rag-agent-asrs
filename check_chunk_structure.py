#!/usr/bin/env python3
"""Check the exact structure of fm_text_chunks and fm_documents."""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_chunk_structure():
    """Check columns and sample data from fm_text_chunks and fm_documents."""
    
    db_url = os.getenv('DATABASE_URL')
    
    try:
        conn = await asyncpg.connect(db_url)
        print("✅ Connected to database\n")
        
        # Check fm_text_chunks structure
        print("📊 Structure of fm_text_chunks:")
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'fm_text_chunks'
            ORDER BY ordinal_position
        """)
        
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        
        # Check fm_documents structure
        print("\n📊 Structure of fm_documents:")
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'fm_documents'
            ORDER BY ordinal_position
        """)
        
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        
        # Get sample data
        print("\n📊 Sample fm_text_chunks data:")
        sample = await conn.fetch("""
            SELECT id, doc_id, content_type, chunk_summary, embedding IS NOT NULL as has_embedding
            FROM fm_text_chunks
            LIMIT 3
        """)
        
        for row in sample:
            print(f"\n  Chunk ID: {row['id']}")
            print(f"  Doc ID: {row['doc_id']}")
            print(f"  Content Type: {row['content_type']}")
            print(f"  Has Embedding: {row['has_embedding']}")
            print(f"  Summary: {row['chunk_summary'][:100] if row['chunk_summary'] else 'None'}...")
        
        # Check if embeddings exist
        embedding_count = await conn.fetchval("""
            SELECT COUNT(*) FROM fm_text_chunks WHERE embedding IS NOT NULL
        """)
        print(f"\n📊 Chunks with embeddings: {embedding_count} / 43")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_chunk_structure())