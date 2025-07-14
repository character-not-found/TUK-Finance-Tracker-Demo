# main.py
# Main entry point for the Cash-On-Hand Business Manager Demo.

import uvicorn
import logging
from app.api.routes import app
from app.logging import configure_logging

# Configure logging at the very beginning of the application startup
configure_logging()
logger = logging.getLogger(__name__)

logger.info("Application starting up...")

if __name__ == "__main__":
    # Command to run the FastAPI application using Uvicorn.
    # Host 0.0.0.0 makes it accessible from other devices on the network.
    # Port 8500 is used to avoid conflicts with common ports.
    # reload=True enables hot-reloading during development.
    uvicorn.run("main:app", host="0.0.0.0", port=8500, reload=True)