# app/logging.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def configure_logging():
    """
    Configures application-wide logging to a file and the console.
    Logs are written to 'app.log' within a 'logs' directory located
    one level up from the 'app' directory (i.e., in the 'site' directory).
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Prevent adding duplicate handlers, especially important with uvicorn's --reload
    if not logger.handlers:
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = log_dir / 'app.log'

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=1024 * 1024 * 5, # 5 MB per file
            backupCount=5             # Keep 5 backup log files
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    logging.info("Logging configuration complete.")
