import logging
from logging.handlers import RotatingFileHandler

# Configure logger
log_formatter = logging.Formatter('[%(asctime)s] - %(levelname)s - %(message)s')

# File handler for writing logs to a file
log_file = "audit_logs.log"
file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# Stream handler for sending logs to stdout
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_formatter)
stream_handler.setLevel(logging.INFO)

# Create and configure the logger
logger = logging.getLogger("audit_logger")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)  # Write to file
logger.addHandler(stream_handler)  # Write to stdout
