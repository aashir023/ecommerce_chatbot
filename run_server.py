"""
This script is the entry point for running the FastAPI server.
It uses Uvicorn as the ASGI server to serve the application
defined in src.main:app. The server will listen on
all interfaces (0.0.0.0) and port 8000.
"""

import uvicorn

if __name__ == "__main__":
    print("Starting FastAPI server...")
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
