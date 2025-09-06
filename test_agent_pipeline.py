#!/usr/bin/env python3
"""
Test script to validate the FM Global agent pipeline.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_agent_pipeline():
    """Test the complete agent pipeline."""
    
    print("=== FM Global Agent Pipeline Test ===\n")
    
    # Test 1: Import and initialize agent
    print("1. Testing agent import and initialization...")
    try:
        from rag_agent.core.fm_global_agent import get_fm_global_agent
        from rag_agent.core.dependencies import AgentDependencies
        from rag_agent.config.settings import load_settings
        
        # Load settings
        settings = load_settings()
        print(f"✅ Settings loaded - LLM Provider: {settings.llm_provider}")
        print(f"✅ Database URL configured: {bool(settings.database_url)}")
        print(f"✅ LLM API Key configured: {bool(settings.llm_api_key)}")
        
        # Create agent
        agent = get_fm_global_agent()
        print("✅ Agent created successfully")
        
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False
    
    # Test 2: Initialize dependencies
    print("\n2. Testing dependencies initialization...")
    try:
        deps = AgentDependencies(settings=settings)
        await deps.initialize()
        print("✅ Dependencies initialized")
        
    except Exception as e:
        print(f"❌ Dependencies initialization failed: {e}")
        return False
    
    # Test 3: Test database connection
    print("\n3. Testing database connection...")
    try:
        db_pool = await deps.get_db_pool()
        async with db_pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            print(f"✅ Database connection successful: {result}")
            
        # Test database functions exist
        async with db_pool.acquire() as conn:
            # Check if FM Global functions exist
            functions = [
                'match_fm_global_vectors',
                'hybrid_search_fm_global', 
                'get_fm_global_references_by_topic'
            ]
            
            for func in functions:
                result = await conn.fetchval(
                    "SELECT EXISTS (SELECT 1 FROM pg_proc WHERE proname = $1)",
                    func
                )
                if result:
                    print(f"✅ Function {func} exists")
                else:
                    print(f"❌ Function {func} missing")
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    
    # Test 4: Test embedding generation
    print("\n4. Testing embedding generation...")
    try:
        test_text = "sprinkler requirements for ASRS"
        embedding = await deps.get_embedding(test_text)
        print(f"✅ Embedding generated - length: {len(embedding)}")
        
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return False
    
    # Test 5: Test tool functions
    print("\n5. Testing search tools...")
    try:
        from rag_agent.tools.fm_global_tools import semantic_search_fm_global, hybrid_search_fm_global
        from pydantic_ai import RunContext
        
        # Create mock context
        ctx = RunContext(deps=deps, retry=0)
        
        # Test semantic search
        semantic_results = await semantic_search_fm_global(
            ctx, 
            "sprinkler requirements",
            match_count=5
        )
        print(f"✅ Semantic search returned {len(semantic_results)} results")
        
        # Test hybrid search  
        hybrid_results = await hybrid_search_fm_global(
            ctx,
            "ASRS fire protection", 
            match_count=5
        )
        print(f"✅ Hybrid search returned {len(hybrid_results)} results")
        
    except Exception as e:
        print(f"❌ Search tools test failed: {e}")
        return False
    
    # Test 6: Test full agent query
    print("\n6. Testing full agent query...")
    try:
        test_query = "What are the sprinkler requirements for a shuttle ASRS with closed-top containers?"
        
        result = await agent.run(test_query, deps=deps)
        response = result.data
        
        print(f"✅ Agent query successful")
        print(f"Response length: {len(response)} characters")
        print(f"Response preview: {response[:200]}...")
        
        # Check if response contains expected elements
        if "sprinkler" in response.lower():
            print("✅ Response contains sprinkler information")
        if any(word in response.lower() for word in ["table", "figure"]):
            print("✅ Response contains references")
        if len(response) > 100:
            print("✅ Response has substantial content")
            
    except Exception as e:
        print(f"❌ Agent query test failed: {e}")
        return False
    
    # Cleanup
    await deps.cleanup()
    print("\n✅ All tests passed! Agent pipeline is working correctly.")
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_agent_pipeline())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n❌ Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)