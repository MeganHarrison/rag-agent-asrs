#!/usr/bin/env python3
"""Check the structure of existing FM Global tables."""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_table_structure():
    """Check the columns of existing FM Global tables."""
    
    db_url = os.getenv('DATABASE_URL')
    
    try:
        conn = await asyncpg.connect(db_url)
        print("✅ Connected to database\n")
        
        # Check fm_global_tables structure
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'fm_global_tables'
            ORDER BY ordinal_position;
        """)
        
        print("📊 Structure of fm_global_tables:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        
        # Check fm_global_figures structure
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'fm_global_figures'
            ORDER BY ordinal_position;
        """)
        
        print("\n📊 Structure of fm_global_figures:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        
        # Check fm_global_vectors structure
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'fm_global_vectors'
            ORDER BY ordinal_position;
        """)
        
        if columns:
            print("\n📊 Structure of fm_global_vectors:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        else:
            print("\n❌ fm_global_vectors table not found")
        
        # Check sample data
        print("\n📊 Sample data in fm_global_tables:")
        rows = await conn.fetch("SELECT * FROM fm_global_tables LIMIT 2")
        for row in rows:
            print(f"  - Table {row.get('table_number', 'N/A')}: {row.get('title', 'N/A')}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_table_structure())