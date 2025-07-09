# main.py
# Import the FastAPI app instance from the new location
from app.api.routes import app # Import the app instance directly
# Updated imports to reflect model renames and additions
from app.models import FixedCost, DailyExpense, Income, CostFrequency, ExpenseCategory
from app import database # Keep database import for example usage
from app.logging import configure_logging # Import the logging configuration function

import uvicorn
import logging # Still need logging for logger.info calls in this file

# Configure logging at the very beginning of the application startup
configure_logging()
logger = logging.getLogger(__name__) # Get a logger for this specific module

logger.info("Web Application starting up...")

if __name__ == "__main__":
    # To run the FastAPI app, you would typically use:
    # uvicorn app.api.routes:app --reload --host 0.0.0.0 --port 8000
    # Or if you want to run it directly from main.py for development:
    import uvicorn
    uvicorn.run("app.api.routes:app", host="0.0.0.0", port=8000, reload=True)