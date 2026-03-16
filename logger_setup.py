# logger_setup.py
# Logging configuration for SSGADD data collection

import os
import logging
import config


def setup_logging():
    """
    Setup logging configuration for the application.
    Creates log directory and configures both file and console handlers.
    """

    # Create log directory if it doesn't exist
    os.makedirs(config.LOG_DIR, exist_ok=True)

    # Generate log filename
    log_filename = config.LOG_FILE_PATTERN.format(timestamp=config.RUN_TIMESTAMP)
    log_path = os.path.join(config.LOG_DIR, log_filename)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(config.LOG_LEVEL)

    # Remove any existing handlers
    root_logger.handlers = []

    # Create formatters
    formatter = logging.Formatter(
        config.LOG_FORMAT,
        datefmt=config.LOG_DATE_FORMAT
    )

    # File handler
    if config.LOG_TO_FILE:
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(config.LOG_LEVEL)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Console handler
    if config.LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(config.LOG_LEVEL)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Log initial setup message
    root_logger.info(f"Logging initialized - Log file: {log_path}")

    return root_logger


if __name__ == '__main__':
    # Test logging setup
    logger = setup_logging()
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    logger.critical("This is a CRITICAL message")
