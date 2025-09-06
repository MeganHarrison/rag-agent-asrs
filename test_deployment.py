#!/usr/bin/env python3
"""
Test script for validating Render deployment of RAG Agent services.

This script tests both the main RAG API and vectorization API endpoints
to ensure they are working correctly after deployment.
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, Optional

# Configuration
RAG_API_URL = "https://rag-agent-api.onrender.com"
VECTORIZATION_API_URL = "https://rag-vectorization-api.onrender.com"

# Test data
TEST_CHAT_MESSAGE = {
    "message": "What projects are currently active in the system?",
    "conversation_history": [],
    "session_id": "test-session-123"
}

TEST_DOCUMENT = {
    "content": "This is a test document about project management. It contains information about timelines, budgets, and team members.",
    "title": "Test Project Document",
    "source": "test_deployment.py",
    "document_type": "test",
    "metadata": {
        "author": "Test System",
        "created_at": "2025-09-05",
        "project_id": "test-project-001"
    }
}

async def test_endpoint_health(session: aiohttp.ClientSession, url: str, name: str) -> bool:
    """Test if an endpoint is healthy and responding."""
    try:
        print(f"\n🔍 Testing {name} health endpoint...")
        async with session.get(f"{url}/health") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ {name} is healthy: {data}")
                return True
            else:
                print(f"❌ {name} health check failed with status {response.status}")
                return False
    except Exception as e:
        print(f"❌ {name} health check failed with error: {str(e)}")
        return False

async def test_rag_chat(session: aiohttp.ClientSession) -> bool:
    """Test the RAG chat functionality."""
    try:
        print(f"\n🔍 Testing RAG chat endpoint...")
        
        headers = {"Content-Type": "application/json"}
        async with session.post(
            f"{RAG_API_URL}/chat",
            json=TEST_CHAT_MESSAGE,
            headers=headers
        ) as response:
            
            if response.status == 200:
                data = await response.json()
                print(f"✅ RAG chat successful:")
                print(f"   Response: {data.get('response', 'No response field')[:100]}...")
                print(f"   Session ID: {data.get('session_id', 'None')}")
                return True
            else:
                text = await response.text()
                print(f"❌ RAG chat failed with status {response.status}: {text}")
                return False
                
    except Exception as e:
        print(f"❌ RAG chat test failed with error: {str(e)}")
        return False

async def test_vectorization(session: aiohttp.ClientSession) -> bool:
    """Test the vectorization functionality."""
    try:
        print(f"\n🔍 Testing vectorization endpoint...")
        
        headers = {"Content-Type": "application/json"}
        async with session.post(
            f"{VECTORIZATION_API_URL}/vectorize",
            json=TEST_DOCUMENT,
            headers=headers
        ) as response:
            
            if response.status == 200:
                data = await response.json()
                print(f"✅ Vectorization successful:")
                print(f"   Status: {data.get('status', 'No status field')}")
                print(f"   Document ID: {data.get('document_id', 'None')}")
                print(f"   Chunks created: {data.get('chunks_created', 0)}")
                return True
            else:
                text = await response.text()
                print(f"❌ Vectorization failed with status {response.status}: {text}")
                return False
                
    except Exception as e:
        print(f"❌ Vectorization test failed with error: {str(e)}")
        return False

async def test_streaming_chat(session: aiohttp.ClientSession) -> bool:
    """Test the streaming chat functionality."""
    try:
        print(f"\n🔍 Testing streaming chat endpoint...")
        
        headers = {"Content-Type": "application/json"}
        async with session.post(
            f"{RAG_API_URL}/chat/stream",
            json=TEST_CHAT_MESSAGE,
            headers=headers
        ) as response:
            
            if response.status == 200:
                print("✅ Streaming chat started successfully")
                
                # Read first few chunks
                chunk_count = 0
                async for line in response.content:
                    if line.strip():
                        try:
                            data = json.loads(line.decode())
                            chunk_count += 1
                            if chunk_count <= 3:  # Only print first few chunks
                                print(f"   Chunk {chunk_count}: {data}")
                        except:
                            pass  # Skip non-JSON lines
                        
                        if chunk_count >= 5:  # Stop after a few chunks
                            break
                
                print(f"✅ Received {chunk_count} streaming chunks")
                return True
            else:
                text = await response.text()
                print(f"❌ Streaming chat failed with status {response.status}: {text}")
                return False
                
    except Exception as e:
        print(f"❌ Streaming chat test failed with error: {str(e)}")
        return False

async def run_deployment_tests():
    """Run all deployment validation tests."""
    print("🚀 Starting Render Deployment Validation Tests")
    print("=" * 60)
    
    # Track test results
    test_results = {
        "rag_health": False,
        "vectorization_health": False,
        "rag_chat": False,
        "vectorization": False,
        "streaming_chat": False
    }
    
    # Configure session with longer timeout for cold starts
    timeout = aiohttp.ClientTimeout(total=60)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        
        # Test health endpoints first
        test_results["rag_health"] = await test_endpoint_health(
            session, RAG_API_URL, "RAG API"
        )
        test_results["vectorization_health"] = await test_endpoint_health(
            session, VECTORIZATION_API_URL, "Vectorization API"
        )
        
        # Only run functional tests if health checks pass
        if test_results["rag_health"]:
            test_results["rag_chat"] = await test_rag_chat(session)
            test_results["streaming_chat"] = await test_streaming_chat(session)
        
        if test_results["vectorization_health"]:
            test_results["vectorization"] = await test_vectorization(session)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("=" * 60)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Deployment is successful.")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please check the deployment.")
        return False

def print_manual_test_instructions():
    """Print manual testing instructions."""
    print("\n" + "=" * 60)
    print("🧪 Manual Testing Instructions:")
    print("=" * 60)
    
    print("\n1. Test RAG API Chat:")
    print(f"   curl -X POST {RAG_API_URL}/chat \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{")
    print('          "message": "What projects are in the system?",')
    print('          "conversation_history": [],')
    print('          "session_id": "test-123"')
    print("        }'")
    
    print("\n2. Test Vectorization API:")
    print(f"   curl -X POST {VECTORIZATION_API_URL}/vectorize \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{")
    print('          "content": "Test document content",')
    print('          "title": "Test Doc",')
    print('          "source": "manual_test"')
    print("        }'")
    
    print("\n3. Check Health Endpoints:")
    print(f"   curl {RAG_API_URL}/health")
    print(f"   curl {VECTORIZATION_API_URL}/health")

if __name__ == "__main__":
    print("RAG Agent Deployment Test Suite")
    print(f"Testing deployment at:")
    print(f"  - RAG API: {RAG_API_URL}")
    print(f"  - Vectorization API: {VECTORIZATION_API_URL}")
    print()
    
    try:
        success = asyncio.run(run_deployment_tests())
        
        if not success:
            print_manual_test_instructions()
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {str(e)}")
        print_manual_test_instructions()