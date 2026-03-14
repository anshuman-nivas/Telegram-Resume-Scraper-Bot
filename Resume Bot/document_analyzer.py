# DocumentAnalyzer: Extracts text from documents (PDF, DOCX, images)
import os
import requests
from logger import logger
from utils import extract_text, MIN_OCR_IMAGE_SIZE
from config import OCR_API_URL

class DocumentAnalyzer:

    def __init__(self):
        logger.info("DocumentAnalyzer initialized (API OCR mode)")

    def extract(self, path):

        ext = os.path.splitext(path)[1].lower()

        # -----------------------------
        # PDF / DOCX (LOCAL EXTRACTION)
        # -----------------------------
        if ext in [".pdf", ".docx"]:
            text, page_count = extract_text(path)
            return text, page_count

        # -----------------------------
        # IMAGE OCR (API CALL)
        # -----------------------------
        if ext in [".jpg", ".jpeg", ".png"]:
            return self._ocr_via_api(path)

        return "", 0

    def _ocr_via_api(self, path):

        try:
            size = os.path.getsize(path)
            if size < MIN_OCR_IMAGE_SIZE:
                logger.info("Image too small → skipping OCR")
                return "", 1

            logger.info(f"Sending image to OCR API → {path}")

            for attempt in range(3):

                try:
                    with open(path, "rb") as f:
                        files = {"file": f}
                        response = requests.post(
                            OCR_API_URL,
                            files=files,
                            timeout=180
                        )

                    if response.status_code != 200:
                        logger.error("OCR API returned non-200")
                        continue

                    try:
                        data = response.json()
                    except Exception:
                        logger.error("OCR API invalid JSON")
                        continue

                    if not data.get("success"):
                        logger.error(f"OCR failure → {data}")
                        continue

                    text = data.get("text", "")
                    logger.info(f"OCR text length: {len(text)}")

                    return text.lower(), 1

                except Exception as e:
                    logger.warning(f"OCR retry {attempt+1}/3 failed")

            logger.error("OCR API failed after retries")
            return "", 1

        except Exception:
            logger.exception("OCR API call failed")
            return "", 1
        