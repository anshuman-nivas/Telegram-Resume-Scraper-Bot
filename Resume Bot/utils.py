# utils.py
import os
import re
import hashlib
import fitz  # PyMuPDF
import docx
from logger import logger
MIN_OCR_IMAGE_SIZE = 50_000    # 50 KB


class JoinStatus:
    YES = "yes"
    DUPLICATE = "duplicate"
    EXPIRED = "expired"
    INVALID = "invalid"
    RETRY = "retry"
    FAILED = "failed"
    PREVIEW = "preview"

def safe_group_folder(name: str) -> str:
    name = (name or "").strip().lower()
    name = re.sub(r"[^\w\- ]+", "", name)
    name = re.sub(r"\s+", "_", name)
    return name[:64] or "unknown_group"

def log_ignored(reason: str, filename: str):
    logger.info(f"IGNORED [{reason}] → {filename}")

def safe_int(val, default=0):
    try:
        return int(val)
    except Exception:
        return default

def compute_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _fix_character_split(text: str) -> str:
    """
    Fix PDFs where characters appear one-per-line.
    """
    lines = text.splitlines()

    if not lines:
        return text

    # if most lines are single characters -> reconstruct
    short_lines = sum(1 for l in lines if len(l.strip()) <= 2)

    if short_lines > len(lines) * 0.6:
        return "".join(lines)

    return text


def extract_text(path):
    """
    Extract text from PDF or DOCX with cleanup
    Returns: (text, page_count)
    """

    if path.lower().endswith(".pdf"):

        doc = fitz.open(path)
        pages = []

        for page in doc:
            pages.append(page.get_text("text"))

        text = "\n".join(pages)
        page_count = len(doc)

    elif path.lower().endswith(".docx"):

        document = docx.Document(path)
        paragraphs = [p.text for p in document.paragraphs]

        text = "\n".join(paragraphs)
        page_count = 1

    else:
        return "", 0

    # ---------------------------------------
    # CLEANUP PIPELINE
    # ---------------------------------------

    # fix character-per-line PDFs
    text = _fix_character_split(text)

    # normalize whitespace
    text = " ".join(text.split())

    # preserve email/phone characters
    text = re.sub(r"[^a-zA-Z0-9@\.\+\-\s]", " ", text)

    # repair broken emails like "name @ gmail . com"
    text = re.sub(r"\s*@\s*", "@", text)
    text = re.sub(r"\s*\.\s*", ".", text)

    return text.lower(), page_count

def normalize_ocr_text(text: str) -> str:
    """
    Normalize noisy OCR output before classification.
    This is CRITICAL for resume detection accuracy.
    """

    text = text.lower()

    # fix spaced email patterns
    text = re.sub(r"\s*@\s*", "@", text)
    text = re.sub(r"\s*\.\s*", ".", text)

    # fix common OCR domain mistakes
    domain_fixes = {
        "gmai.com": "gmail.com",
        "gmial.com": "gmail.com",
        "gmaill.com": "gmail.com",
        "gma1l.com": "gmail.com",
        "gmall.com": "gmail.com",
        "outlok.com": "outlook.com",
        "yaho.com": "yahoo.com"
    }

    for wrong, correct in domain_fixes.items():
        text = text.replace(wrong, correct)

    # merge split digits
    text = re.sub(r"(\d)\s+(\d)", r"\1\2", text)

    return text

def normalize_telegram_link(link: str):

    if not link:
        return ""

    link = link.strip().lower()

    link = link.replace("https://t.me/s/", "https://t.me/")
    link = link.replace("http://t.me/s/", "https://t.me/")
    link = link.replace("https://telegram.me/", "https://t.me/")

    if "?" in link:
        link = link.split("?")[0]

    parts = link.split("/")
    if len(parts) > 4:
        link = "/".join(parts[:4])

    return link.rstrip("/")

