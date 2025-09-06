#!/usr/bin/env python3
"""Ultra-simple server for debugging Railway deployment."""

import os
import sys

print(f"Python version: {sys.version}", flush=True)
print(f"PORT env: {os.getenv('PORT', 'NOT SET')}", flush=True)
print(f"Current directory: {os.getcwd()}", flush=True)
print(f"Files in directory: {os.listdir('.')}", flush=True)

try:
    from fastapi import FastAPI
    import uvicorn
    
    print("FastAPI and uvicorn imported successfully", flush=True)
    
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {"status": "healthy", "message": "Simple server is running!"}
    
    @app.get("/health")
    async def health():
        return {"status": "ok"}
    
    port = int(os.getenv("PORT", 8000))
    print(f"Starting server on port {port}", flush=True)
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    
except Exception as e:
    print(f"ERROR: {e}", flush=True)
    print(f"Error type: {type(e).__name__}", flush=True)
    
    # Start a basic HTTP server as fallback
    from http.server import HTTPServer, BaseHTTPRequestHandler
    
    class SimpleHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"healthy","mode":"fallback"}')
    
    port = int(os.getenv("PORT", 8000))
    print(f"Starting fallback HTTP server on port {port}", flush=True)
    
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()