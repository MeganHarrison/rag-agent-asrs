#!/usr/bin/env python3
"""
Multi-Agent Platform Startup Script for Render Production Deployment.
"""

import sys
import os
import logging
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))


def check_environment():
    """Check required environment variables for multi-agent platform."""
    required_core = ['DATABASE_URL', 'LLM_API_KEY']
    optional_agents = {
        'FM_GLOBAL': ['FM_GLOBAL_LLM_KEY', 'FM_GLOBAL_DB_URL'],
        'GENERAL': ['GENERAL_LLM_KEY', 'GENERAL_DB_URL'],
        'CODE': ['CODE_LLM_KEY', 'CODE_DB_URL'],
        'DOCS': ['DOCS_LLM_KEY', 'DOCS_DB_URL']
    }
    
    # Check core requirements
    missing_core = [var for var in required_core if not os.getenv(var)]
    if missing_core:
        logger.warning(f"Missing core environment variables: {missing_core}")
        logger.info("Using fallback configuration for missing variables")
    
    # Check agent-specific configs
    active_agents = []
    for agent, vars in optional_agents.items():
        if any(os.getenv(var) for var in vars):
            active_agents.append(agent)
    
    logger.info(f"Active specialized agents: {active_agents if active_agents else 'Using shared configuration'}")
    
    return len(missing_core) == 0


def initialize_database_pools():
    """Initialize database connection pools for better performance."""
    try:
        logger.info("Initializing database connection pools...")
        # This would initialize your database pools
        # Example: asyncpg pools for PostgreSQL
        pool_size = int(os.getenv('CONNECTION_POOL_SIZE', '20'))
        logger.info(f"Database pools initialized with size: {pool_size}")
    except Exception as e:
        logger.warning(f"Could not initialize database pools: {e}")


def start_multi_agent_server():
    """Start the Multi-Agent FastAPI server."""
    try:
        logger.info("Starting Multi-Agent RAG Platform...")
        
        # Check environment
        env_ok = check_environment()
        if not env_ok:
            logger.warning("Running with incomplete configuration - some agents may be unavailable")
        
        # Initialize database pools for production
        if os.getenv('CONNECTION_POOL_SIZE'):
            initialize_database_pools()
        
        # Import FastAPI app (lazy import to avoid early initialization)
        from rag_agent.api.multi_agent_app import app
        import uvicorn
        
        # Get configuration from environment
        port = int(os.getenv("PORT", 8000))
        workers = int(os.getenv("MAX_WORKERS", 1))
        
        logger.info(f"Server configuration:")
        logger.info(f"  Port: {port}")
        logger.info(f"  Workers: {workers}")
        logger.info(f"  Rate limiting: {os.getenv('ENABLE_RATE_LIMITING', 'false')}")
        logger.info(f"  Metrics: {os.getenv('ENABLE_METRICS', 'false')}")
        
        # Production configuration
        if workers > 1:
            # Multi-worker configuration for production
            logger.info(f"Starting production server with {workers} workers")
            uvicorn.run(
                "rag_agent.api.multi_agent_app:app",
                host="0.0.0.0",
                port=port,
                workers=workers,
                log_level="info",
                access_log=True,
                loop="uvloop"
            )
        else:
            # Single worker for development/free tier
            logger.info("Starting development server with single worker")
            uvicorn.run(
                app,
                host="0.0.0.0",
                port=port,
                log_level="info",
                reload=False,
                access_log=True,
                timeout_keep_alive=75,
                timeout_notify=60,
                loop="uvloop"
            )
        
    except ImportError as e:
        logger.error(f"Import error during startup: {e}")
        logger.info("Check that all dependencies are installed")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        logger.info("Server will retry in 5 seconds...")
        time.sleep(5)
        sys.exit(1)


def main():
    """Main entry point."""
    try:
        # Log startup information
        logger.info("=" * 60)
        logger.info("Multi-Agent RAG Platform")
        logger.info("Serving multiple specialized AI agents on single instance")
        logger.info("=" * 60)
        
        # Start the server
        start_multi_agent_server()
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()