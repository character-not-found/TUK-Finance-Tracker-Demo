# app/logging.py
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path

def configure_logging():
    """
    Configures the application-wide logging.
    Logs will be written to a file named 'app.log' inside a 'logs' directory
    within the 'site' directory (one level up from 'app').
    """
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO) # Set the minimum level to INFO

    # Ensure handlers are not duplicated if called multiple times (e.g., in development with reload)
    if not logger.handlers:
        # Define log file path
        # Path(__file__) is app/logging.py
        # Path(__file__).parent is app/
        # Path(__file__).parent.parent is site/
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True) # Create the logs directory if it doesn't exist
        log_file_path = log_dir / 'app.log'

        # Create a formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Create a file handler for logging to a file
        # Use RotatingFileHandler to limit log file size and keep backups
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=1024 * 1024 * 5, # 5 MB
            backupCount=5 # Keep up to 5 backup log files
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Create a stream handler for logging to the console (stdout)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    logging.info("Logging configured successfully.")

# You can call configure_logging() directly here if you want it to run
# as soon as this module is imported. However, it's often better to call it
# explicitly from your main application entry point (e.g., main.py)
# to ensure it's set up before any other application logic runs.
