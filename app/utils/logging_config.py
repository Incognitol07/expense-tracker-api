# app/utils/logging_config.py

import logging
from logging.handlers import RotatingFileHandler

# Configure logger
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_file = "audit_logs.log"

file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

logger = logging.getLogger("audit_logger")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
