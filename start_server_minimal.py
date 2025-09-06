#!/usr/bin/env python3
"""
Minimal server startup for Railway/Render deployment.
Uses only core dependencies from requirements-production.txt.
"""

import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def start_server():
    """Start the minimal FastAPI server."""
    try:
        logger.info("Starting FM Global Expert server (minimal)...")
        
        # Get port from environment
        port = int(os.getenv("PORT", 8000))
        logger.info(f"PORT environment variable: {port}")
        
        # Try to import the ultra_safe app first
        try:
            from rag_agent.api.fm_global_app_ultra_safe import app
            logger.info("Successfully imported fm_global_app_ultra_safe")
        except ImportError as e:
            logger.warning(f"Could not import fm_global_app_ultra_safe: {e}")
            logger.info("Falling back to basic app...")
            
            # Create a minimal app if import fails
            from fastapi import FastAPI
            from fastapi.middleware.cors import CORSMiddleware
            
            app = FastAPI(title="FM Global Expert API", version="1.0.0")
            
            # Add CORS
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            
            @app.get("/")
            async def root():
                return {
                    "status": "healthy",
                    "service": "FM Global Expert (minimal)",
                    "note": "Running in fallback mode"
                }
            
            @app.get("/health")
            async def health():
                return {"status": "healthy"}
        
        # Import uvicorn and run
        import uvicorn
        
        logger.info(f"Starting Uvicorn on 0.0.0.0:{port}")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            # Don't use uvloop if not available
            loop="asyncio"  # Changed from "uvloop" to "asyncio"
        )
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)