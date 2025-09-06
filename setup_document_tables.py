#!/usr/bin/env python3
"""Setup fm_documents and fm_text_chunks tables in Supabase."""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def setup_document_tables():
    """Create fm_documents and fm_text_chunks tables."""
    
    db_url = os.getenv('DATABASE_URL')
    
    try:
        conn = await asyncpg.connect(db_url)
        print("✅ Connected to database")
        
        # Read SQL file
        with open('sql/fm_documents_schema.sql', 'r') as f:
            sql = f.read()
        
        # Execute SQL
        await conn.execute(sql)
        print("✅ Document tables created successfully")
        
        # Check the tables
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name IN ('fm_documents', 'fm_text_chunks')
            ORDER BY table_name
        """)
        
        print("\n📊 Created tables:")
        for table in tables:
            print(f"  - {table['table_name']}")
            
            # Count records
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table['table_name']}")
            print(f"    Records: {count}")
        
        await conn.close()
        print("\n✅ Setup complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(setup_document_tables())