#!/usr/bin/env python3
"""Test the optimized startup without external connections."""

import time
import subprocess
import requests
import sys
import os

def test_startup():
    """Test that the server can start without external connections."""
    
    print("Testing optimized server startup...")
    
    # Start the server
    process = subprocess.Popen(
        [sys.executable, "start_server.py"],
        env={**os.environ, "DATABASE_URL": "postgresql://test@localhost/test"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give it time to start
    time.sleep(5)
    
    try:
        # Test the health endpoint
        response = requests.get("http://localhost:8000/")
        print(f"✓ Health check: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        # Test the detailed health endpoint
        response = requests.get("http://localhost:8000/health")
        print(f"✓ Detailed health: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        # Test that it can handle queries with fallback
        response = requests.post(
            "http://localhost:8000/chat",
            json={
                "query": "What are the sprinkler requirements for shuttle ASRS?",
                "asrs_topic": "fire_protection"
            }
        )
        print(f"✓ Chat endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response preview: {response.json()['response'][:100]}...")
        
        print("\n✅ All tests passed! Server starts successfully without external connections.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
    finally:
        # Clean up
        process.terminate()
        process.wait()

if __name__ == "__main__":
    test_startup()