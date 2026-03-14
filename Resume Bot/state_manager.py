# state_manager.py
import json
import os
import sys
import time
from threading import Lock
from datetime import datetime
from logger import logger

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATE_DIR = os.path.join(BASE_DIR, "state")
os.makedirs(STATE_DIR, exist_ok=True)

class StateManager:

    STATE_FILE = os.path.join(STATE_DIR, "runtime_state.json")
    def __init__(self):
        self.lock = Lock()
        self.state = self._load()
 
    # -----------------------------
    # LOAD
    # -----------------------------
    def _load(self):

        if not os.path.exists(self.STATE_FILE):
            return {
                "groups": {},
                "total_processed": 0
            }

        try:
            with open(self.STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {
                "groups": {},
                "total_processed": 0
            }

    # -----------------------------
    # ATOMIC SAVE
    # -----------------------------
    def _save(self):

        tmp = self.STATE_FILE + ".tmp"

        with open(tmp, "w") as f:
            json.dump(self.state, f, indent=2)

        for _ in range(5):  # retry up to 5 times
            try:
                os.replace(tmp, self.STATE_FILE)
                return
            except PermissionError:
                time.sleep(0.1)

        logger.info("Failed to update runtime_state.json after retries")

    # -----------------------------
    # ENSURE GROUP
    # -----------------------------
    def _ensure_group(self, group_link):
        if group_link not in self.state["groups"]:
            self.state["groups"][group_link] = {
                "last_scanned_id": 0,
                "total_resumes": 0,
                "last_scanned_time": ""
            }

        return group_link

    # -----------------------------
    # CURSOR UPDATE
    # -----------------------------
    def mark_message_seen(self, group_link, message_id):

        with self.lock:
            group_link = self._ensure_group(group_link)

            g = self.state["groups"][group_link]
            
            g["last_scanned_id"] = max(
                g["last_scanned_id"],
                message_id
            )
            g["last_scanned_time"] = datetime.utcnow().isoformat()

            self._save()

    # -----------------------------
    # RESUME COUNT
    # -----------------------------
    def increment_resume(self, group_link):

        with self.lock:
            group_link = self._ensure_group(group_link)

            g = self.state["groups"][group_link]
            g["total_resumes"] += 1

            self._save()

    # -----------------------------
    # TOTAL DOCUMENTS PROCESSED
    # -----------------------------
    def increment_processed(self):

        with self.lock:

            self.state["total_processed"] = (
                self.state.get("total_processed", 0) + 1
            )

            self._save()

            return self.state["total_processed"]
        
    # -----------------------------       
    def get_total_processed(self):
        return self.state.get("total_processed", 0)
    
    # -----------------------------
    def get_last_scanned(self, group_link):
        return self.state["groups"].get(
            group_link, {}
        ).get("last_scanned_id", 0)

    # -----------------------------
    def snapshot(self):
        return self.state["groups"]