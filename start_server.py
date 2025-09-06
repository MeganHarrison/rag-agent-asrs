#!/usr/bin/env python3
"""
Optimized server startup for Render deployment.
Includes lazy initialization and proper error handling.
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
    """Check required environment variables."""
    required_vars = ['DATABASE_URL', 'LLM_API_KEY']
    missing = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        logger.warning(f"Missing environment variables: {missing}")
        logger.info("Server will start but some features may be unavailable")
    
    return len(missing) == 0


def start_server():
    """Start the FastAPI server with proper error handling."""
    try:
        logger.info("Starting FM Global Expert RAG Agent Server...")
        
        # Check environment
        env_ok = check_environment()
        if not env_ok:
            logger.warning("Running with incomplete configuration")
        
        # Import FastAPI app (lazy import to avoid early initialization)
        # Use the regular app for full functionality
        from rag_agent.api.fm_global_app import app
        import uvicorn
        
        logger.info("Server initialization complete")
        
        # Get port from environment (Render sets PORT)
        port = int(os.getenv("PORT", 8000))
        logger.info(f"Starting Uvicorn server on 0.0.0.0:{port}")
        
        # Run the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            reload=False,
            access_log=True,
            # timeout_notify removed - not available in all uvicorn versions
            timeout_keep_alive=75,
            loop="uvloop"
        )
        
    except ImportError as e:
        logger.error(f"Import error during startup: {e}")
        logger.info("Attempting to install missing dependencies...")
        os.system("pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        logger.info("Server will retry in 5 seconds...")
        time.sleep(5)
        sys.exit(1)


if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)