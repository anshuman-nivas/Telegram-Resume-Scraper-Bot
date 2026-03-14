# identity_manager.py
import os
import json
import re
from datetime import datetime
from threading import Lock
import sys

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATE_DIR = os.path.join(BASE_DIR, "state")
os.makedirs(STATE_DIR, exist_ok=True)

class IdentityManager:

    STORE_FILE = os.path.join(STATE_DIR, "identity_store.json")
    EMAIL_REGEX = re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    )

    PHONE_REGEX = re.compile(
        r"\+?\d[\d\-\s]{8,15}\d"
    )

    def __init__(self):
        self.lock = Lock()
        self.store = self._load()

    # -------------------------------------------------
    # LOAD STORE
    # -------------------------------------------------

    def _load(self):

        if not os.path.exists(self.STORE_FILE):
            return {}

        try:
            with open(self.STORE_FILE, "r") as f:
                return json.load(f)

        except Exception:
            return {}

    # -------------------------------------------------
    # ATOMIC SAVE
    # -------------------------------------------------

    def _save(self):

        tmp = self.STORE_FILE + ".tmp"

        with open(tmp, "w") as f:
            json.dump(self.store, f, indent=2)

        os.replace(tmp, self.STORE_FILE)

    # -------------------------------------------------
    # NORMALIZE EMAIL
    # -------------------------------------------------

    def normalize_email(self, email):

        if not email:
            return None

        return email.strip().lower()

    # -------------------------------------------------
    # NORMALIZE PHONE
    # -------------------------------------------------

    def normalize_phone(self, phone):

        if not phone:
            return None

        phone = re.sub(r"\D", "", phone)

        if len(phone) > 10:
            phone = phone[-10:]

        if len(phone) < 8:
            return None

        return phone

    # -------------------------------------------------
    # EXTRACT IDENTITY
    # -------------------------------------------------

    def extract_identity(self, text):

        email = None
        phone = None

        email_match = self.EMAIL_REGEX.search(text)

        if email_match:
            email = self.normalize_email(email_match.group())

        phone_match = self.PHONE_REGEX.search(text)

        if phone_match:
            phone = self.normalize_phone(phone_match.group())

        return self._build_key(email, phone)

    # -------------------------------------------------
    # BUILD KEY
    # -------------------------------------------------

    def _build_key(self, email, phone):

        if email and phone:
            return f"{email}|{phone}"

        if email:
            return email

        if phone:
            return phone

        return None

    # -------------------------------------------------
    # CHECK EXISTING IDENTITY
    # -------------------------------------------------

    def exists(self, identity):

        if not identity:
            return False

        return identity in self.store

    # -------------------------------------------------
    # GET EXISTING FILE
    # -------------------------------------------------

    def get_existing_file(self, identity):

        data = self.store.get(identity)

        if not data:
            return None

        return data.get("file")

    # -------------------------------------------------
    # REGISTER NEW
    # -------------------------------------------------

    def register(self, identity, file_path, group):

        if not identity:
            return

        with self.lock:

            self.store[identity] = {
                "file": file_path,
                "group": group,
                "timestamp": datetime.utcnow().isoformat()
            }

            self._save()

    # -------------------------------------------------
    # REPLACE EXISTING
    # -------------------------------------------------

    def replace(self, identity, new_file, group):

        with self.lock:

            old = self.store.get(identity)

            if old:

                old_file = old.get("file")

                if old_file and os.path.exists(old_file):

                    try:
                        os.remove(old_file)
                    except Exception:
                        pass

            self.store[identity] = {
                "file": new_file,
                "group": group,
                "timestamp": datetime.utcnow().isoformat()
            }

            self._save()