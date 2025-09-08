#!/usr/bin/env python3
"""Test script to demonstrate the two FM Global prompt modes."""

import asyncio
import json
from rag_agent.core.fm_global_agent import get_fm_global_agent
from rag_agent.core.dependencies import AgentDependencies
from rag_agent.config.settings import load_settings


async def test_expert_mode():
    """Test the expert Q&A mode."""
    print("\n" + "="*50)
    print("TESTING EXPERT Q&A MODE")
    print("="*50 + "\n")
    
    # Create agent in expert mode
    agent = get_fm_global_agent(mode="expert")
    
    # Create dependencies
    settings = load_settings()
    deps = AgentDependencies(settings=settings)
    
    # Test query
    query = "I have a shuttle ASRS with 8ft deep racks and closed-top containers. What figures and tables apply?"
    
    print(f"Query: {query}\n")
    print("Response (Expert Mode):")
    print("-" * 40)
    
    try:
        result = await agent.run(query, deps=deps)
        print(result.data)
    except Exception as e:
        print(f"Error: {e}")
    
    return result.data if 'result' in locals() else None


async def test_guided_mode():
    """Test the guided design process mode."""
    print("\n" + "="*50)
    print("TESTING GUIDED DESIGN PROCESS MODE")
    print("="*50 + "\n")
    
    # Create agent in guided mode
    agent = get_fm_global_agent(mode="guided")
    
    # Create dependencies
    settings = load_settings()
    deps = AgentDependencies(settings=settings)
    
    # Initial query to start the guided process
    query = "I need help designing a sprinkler system for my ASRS warehouse"
    
    print(f"Query: {query}\n")
    print("Response (Guided Mode):")
    print("-" * 40)
    
    try:
        result = await agent.run(query, deps=deps)
        print(result.data)
    except Exception as e:
        print(f"Error: {e}")
    
    return result.data if 'result' in locals() else None


async def main():
    """Run both prompt mode tests."""
    print("\n" + "🚀 FM GLOBAL PROMPT MODE TESTING" + "\n")
    
    # Test expert mode
    expert_response = await test_expert_mode()
    
    # Wait a moment between tests
    await asyncio.sleep(2)
    
    # Test guided mode
    guided_response = await test_guided_mode()
    
    print("\n" + "="*50)
    print("TEST COMPLETE")
    print("="*50)
    
    # Summary
    print("\nSummary:")
    print("- Expert Mode: Provides direct answers with specific references")
    print("- Guided Mode: Leads through step-by-step requirements gathering")
    print("\nBoth modes have access to the same FM Global database and search tools.")


if __name__ == "__main__":
    asyncio.run(main())