# logger.py
import logging
import os
from logging.handlers import RotatingFileHandler
import sys

# -------------------------------------------------
# LOG DIRECTORY SETUP
# -------------------------------------------------
# LOG_DIR = "logs"
# LOG_FILE = "bot.log"

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = "bot.log"

os.makedirs(LOG_DIR, exist_ok=True)
log_path = os.path.join(LOG_DIR, LOG_FILE)

# -------------------------------------------------
# LOGGER INSTANCE
# -------------------------------------------------
logger = logging.getLogger("resume_bot")
logger.setLevel(logging.INFO)

# Prevent duplicate handlers if reloaded
if logger.hasHandlers():
    logger.handlers.clear()

# -------------------------------------------------
# FORMATTER
# -------------------------------------------------
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)

# -------------------------------------------------
# FILE HANDLER (Rotating)
# -------------------------------------------------
file_handler = RotatingFileHandler(
    log_path,
    maxBytes=5 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8"
)
file_handler.setFormatter(formatter)

# -------------------------------------------------
# CONSOLE HANDLER
# -------------------------------------------------
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# -------------------------------------------------
# ADD HANDLERS
# -------------------------------------------------
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.propagate = False