#!/usr/bin/env python3
"""Setup FM Global database functions."""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def setup_functions():
    """Create FM Global database functions."""
    
    db_url = os.getenv('DATABASE_URL')
    
    try:
        conn = await asyncpg.connect(db_url)
        print("✅ Connected to database")
        
        # Read SQL file
        with open('create_fm_functions.sql', 'r') as f:
            sql = f.read()
        
        # Execute SQL
        await conn.execute(sql)
        print("✅ Database functions created successfully")
        
        # Test the functions
        print("\n📊 Testing functions...")
        
        # Test get_fm_global_references_by_topic
        rows = await conn.fetch("SELECT * FROM get_fm_global_references_by_topic('fire', 5)")
        print(f"Found {len(rows)} references for 'fire' topic")
        
        await conn.close()
        print("\n✅ Setup complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(setup_functions())