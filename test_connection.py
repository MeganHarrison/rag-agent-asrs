#!/usr/bin/env python3
"""Test database and LLM connections directly."""

import asyncio
import os
import sys

async def test_connections():
    print("Testing connections...")
    
    # Test environment variables
    print("\n=== Environment Variables ===")
    print(f"DATABASE_URL: {'SET' if os.getenv('DATABASE_URL') else 'NOT SET'}")
    print(f"LLM_API_KEY: {'SET' if os.getenv('LLM_API_KEY') else 'NOT SET'}")
    print(f"OPENAI_API_KEY: {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
    
    # Test database connection
    print("\n=== Database Connection ===")
    try:
        import asyncpg
        db_url = os.getenv('DATABASE_URL')
        if db_url:
            conn = await asyncpg.connect(db_url)
            version = await conn.fetchval('SELECT version()')
            print(f"✓ Connected to PostgreSQL")
            print(f"  Version: {version[:50]}...")
            
            # Test pgvector
            try:
                result = await conn.fetchval("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
                print(f"✓ pgvector extension: {result}")
            except:
                print("✗ pgvector extension not found")
            
            await conn.close()
        else:
            print("✗ DATABASE_URL not set")
    except Exception as e:
        print(f"✗ Database error: {e}")
    
    # Test OpenAI connection
    print("\n=== OpenAI Connection ===")
    try:
        import openai
        api_key = os.getenv('LLM_API_KEY') or os.getenv('OPENAI_API_KEY')
        if api_key:
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Say 'connected'"}],
                max_tokens=10
            )
            print(f"✓ OpenAI connected")
            print(f"  Response: {response.choices[0].message.content}")
        else:
            print("✗ No API key found")
    except Exception as e:
        print(f"✗ OpenAI error: {e}")
    
    # Test imports
    print("\n=== Package Imports ===")
    packages = ['pgvector', 'numpy', 'asyncpg', 'pydantic_ai', 'fastapi']
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"✓ {pkg}")
        except ImportError:
            print(f"✗ {pkg} not installed")

if __name__ == "__main__":
    asyncio.run(test_connections())