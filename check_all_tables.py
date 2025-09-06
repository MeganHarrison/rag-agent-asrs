#!/usr/bin/env python3
"""Check all FM Global related tables in the database."""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_all_tables():
    """Check all FM Global tables and their structure."""
    
    db_url = os.getenv('DATABASE_URL')
    
    try:
        conn = await asyncpg.connect(db_url)
        print("✅ Connected to database\n")
        
        # Get all tables with 'fm' in the name
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND (table_name LIKE 'fm_%' OR table_name LIKE '%fm_%')
            ORDER BY table_name
        """)
        
        print("📊 FM Global related tables:")
        for table in tables:
            table_name = table['table_name']
            print(f"\n📋 {table_name}:")
            
            # Get row count
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
            print(f"   Records: {count}")
            
            # Get columns
            columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = $1
                ORDER BY ordinal_position
                LIMIT 10
            """, table_name)
            
            print("   Columns:")
            for col in columns:
                print(f"     - {col['column_name']}: {col['data_type']}")
        
        # Check specifically for fm_documents and fm_text_chunks
        print("\n" + "="*50)
        print("Checking for document management tables:")
        
        doc_tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name IN ('fm_documents', 'fm_text_chunks')
        """)
        
        if doc_tables:
            print("✅ Document tables found:")
            for table in doc_tables:
                print(f"  - {table['table_name']}")
        else:
            print("❌ fm_documents and fm_text_chunks not found")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_all_tables())