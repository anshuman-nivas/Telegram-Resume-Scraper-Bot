# resume_processor.py

import os
import re
import json
import atexit
from datetime import datetime
import pytz
import sys
from utils import safe_group_folder, log_ignored, compute_hash, normalize_ocr_text
from document_analyzer import DocumentAnalyzer
from processing_tracker import ProcessingTracker
from detection import *

import smtplib
from email.message import EmailMessage

from config import (
    EMAIL_SENDER,
    EMAIL_RECEIVER,
    SMTP_SERVER,
    SMTP_PORT,
    EMAIL_PASSWORD
)

from identity_manager import IdentityManager
from logger import logger


class ResumeProcessor:

    # SEEN_HASHES_FILE = os.path.join(
    #     os.path.dirname(__file__),
    #     "seen_resume_hashes.json"
    # )

    BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
    SEEN_HASHES_FILE = os.path.join(BASE_DIR, "state", "seen_resume_hashes.json")

    def __init__(self, state_manager):

        self.state_manager = state_manager
        self.seen_hashes = self._load_hashes()

        self.analyzer = DocumentAnalyzer()
        self.tracker = ProcessingTracker(state_manager)
        self.identity_manager = IdentityManager()

        atexit.register(self.persist_hashes)

    # -------------------------------------------------
    # LOAD HASH STORE
    # -------------------------------------------------

    def _load_hashes(self):

        if os.path.exists(self.SEEN_HASHES_FILE):

            try:
                with open(self.SEEN_HASHES_FILE, "r") as f:
                    return json.load(f)

            except Exception:
                return {}

        return {}

    # -------------------------------------------------
    # IGNORE HANDLER
    # -------------------------------------------------

    def _ignore(self, reason, filename):

        log_ignored(reason, filename)

        logger.info(f"Document ignored | reason={reason} | file={filename}")

        self.tracker.ignored()
        return

    # -------------------------------------------------
    # SAVE HASH STORE
    # -------------------------------------------------

    def persist_hashes(self):

        try:

            with open(self.SEEN_HASHES_FILE, "w") as f:
                json.dump(self.seen_hashes, f, indent=2)

        except Exception:
            logger.exception("Failed persisting seen_resume_hashes.json")

    # -------------------------------------------------
    # MAIN PROCESSOR
    # -------------------------------------------------

    async def process_document(self, message, group_link, group_title_map):

        filename = None
        success = False

        if message.document:
            for attr in message.document.attributes:
                if hasattr(attr, "file_name"):
                    filename = attr.file_name
                    break

        elif message.photo:
            filename = f"photo_{message.id}.jpg"

        if not filename:
            return False

        logger.info(f"Processing document | file={filename} | message_id={message.id}")

        india = pytz.timezone("Asia/Kolkata")
        today = datetime.now(india).date()
        msg_date = message.date.astimezone(india).date()
        is_today_message = msg_date == today

        ext = os.path.splitext(filename)[1].lower()
        if message.photo:
            ext = ".jpg"

        if ext not in (".pdf", ".docx", ".jpg", ".jpeg", ".png"):
            self._ignore("Unsupported file type", filename)
            return False

        temp_path = None

        try:

            temp_path = await message.download_media(file=f"temp/{message.id}_")

            if not temp_path or not os.path.exists(temp_path):
                self._ignore("Download failed", filename)
                return False

            file_hash = compute_hash(temp_path)
            logger.info(f"File hash computed | {file_hash}")

            if file_hash in self.seen_hashes:
                logger.info("Duplicate detected via file hash")
                self._ignore("Duplicate", filename)
                return True

            text, page_count = self.analyzer.extract(temp_path)

            if isinstance(text, list):
                text = "\n".join(text)

            logger.info(f"Extracted text length: {len(text)}")

            preview = text[:500].replace("\n", " ")
            logger.info("DOCUMENT TEXT START (preview)")
            logger.info(preview)
            logger.info("DOCUMENT TEXT END")

            if page_count > 5:
                self._ignore("Too many pages (>5)", filename)
                return True

            text = normalize_ocr_text(text)

            identity = self.identity_manager.extract_identity(text)
            logger.info(f"Identity extracted: {identity}")

            if is_jd_filename(filename):
                self._ignore("JD filename", filename)
                return True

            result = is_resume_content(text)
            logger.info(f"Classification result: {result}")

            if not result:
                self._ignore("Not a resume (classifier)", filename)
                return True

            group_dir = os.path.join(
                "resumes",
                safe_group_folder(group_title_map[group_link])
            )
            os.makedirs(group_dir, exist_ok=True)

            final_path = os.path.join(group_dir, filename)

            if identity and self.identity_manager.exists(identity):

                logger.info(f"Identity duplicate detected: {identity}")

                os.replace(temp_path, final_path)

                self.identity_manager.replace(
                    identity,
                    final_path,
                    group_link
                )

                self.tracker.saved()
                self.state_manager.increment_resume(group_link)

                success = True
                return True

            if is_today_message:

                logger.info(f"Today's resume → sending email: {filename}")

                await self.send_email(temp_path, filename)

                logger.info(f"Email successfully sent: {filename}")

                if identity:
                    self.identity_manager.register(
                        identity,
                        final_path,
                        group_link
                    )

                self.tracker.saved()
                success = True
                return True

            else:

                os.replace(temp_path, final_path)

                logger.info(f"Saved resume: {final_path}")

                if identity:
                    self.identity_manager.register(
                        identity,
                        final_path,
                        group_link
                    )

                self.tracker.saved()
                self.state_manager.increment_resume(group_link)

                success = True
                return True

        except Exception:
            logger.exception("Error while processing document")
            return False

        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
    # -------------------------------------------------
    # EMAIL SENDER
    # -------------------------------------------------

    async def send_email(self, file_path, filename):

        try:

            msg = EmailMessage()

            msg["Subject"] = "Resume received from Telegram"
            msg["From"] = EMAIL_SENDER
            msg["To"] = EMAIL_RECEIVER

            msg.set_content("A resume was received today from Telegram.")

            with open(file_path, "rb") as f:
                data = f.read()

            msg.add_attachment(
                data,
                maintype="application",
                subtype="octet-stream",
                filename=filename
            )

            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
                smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
                smtp.send_message(msg)
            logger.info(f"Email sent successfully | file={filename}")

        except Exception:
            logger.exception("Email sending failed")