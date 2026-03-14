# config.py
# -------------------------------------------------
# Handles configuration loading for both
# Python script execution and PyInstaller EXE
# -------------------------------------------------

import os
import sys
from dotenv import load_dotenv


# -------------------------------------------------
# DETERMINE BASE DIRECTORY
# -------------------------------------------------

# If running as EXE (PyInstaller)
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)

# If running as normal Python script
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# -------------------------------------------------
# LOAD .env FILE
# -------------------------------------------------

ENV_PATH = os.path.join(BASE_DIR, ".env")

if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
else:
    print("WARNING: .env file not found")


# -------------------------------------------------
# TELEGRAM CONFIG
# -------------------------------------------------

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE = os.getenv("PHONE")


# -------------------------------------------------
# EMAIL CONFIG
# -------------------------------------------------

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))


# -------------------------------------------------
# GOOGLE SHEETS CONFIG
# -------------------------------------------------

GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID")
GOOGLE_SHEETS_WORKSHEET_NAME = os.getenv("GOOGLE_SHEETS_WORKSHEET_NAME")

GOOGLE_SHEETS_CREDENTIALS_PATH = os.path.join(
    BASE_DIR,
    os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
)

OCR_API_URL = os.getenv("OCR_API_URL", "http://127.0.0.1:8001/ocr")