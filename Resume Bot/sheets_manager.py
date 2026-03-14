# sheets_manager.py
import gspread
from google.oauth2.service_account import Credentials
from config import GOOGLE_SHEETS_WORKSHEET_NAME
from utils import normalize_telegram_link, JoinStatus


class SheetsManager:

    RUNTIME_COLUMNS = [
        "last_scanned_message_id",
        "last_scanned_time",
        "total_resumes_fetched",
        "total_processed",
    ]

    # -------------------------------------------------
    def __init__(self, credentials_path, spreadsheet_id,
                 worksheet_name=GOOGLE_SHEETS_WORKSHEET_NAME):

        scope = ["https://www.googleapis.com/auth/spreadsheets"]

        creds = Credentials.from_service_account_file(
            credentials_path,
            scopes=scope
        )

        client = gspread.authorize(creds)

        self.sheet = client.open_by_key(
            spreadsheet_id
        ).worksheet(worksheet_name)

        self._load()
        self._ensure_runtime_columns()

    # -------------------------------------------------
    # LOAD SHEET CACHE
    # -------------------------------------------------
    def _load(self):

        self.headers = self.sheet.row_values(1)
        self.col_index = {h: i + 1 for i, h in enumerate(self.headers)}

        self.records = self.sheet.get_all_records()
        self.row_map = {}

        for idx, record in enumerate(self.records, start=2):

            raw_link = record.get("Telegram Link")
            if not raw_link:
                continue

            link = normalize_telegram_link(raw_link)
            self.row_map[link] = idx

    # -------------------------------------------------
    # ENSURE RUNTIME COLUMNS
    # -------------------------------------------------
    def _ensure_runtime_columns(self):

        for col in self.RUNTIME_COLUMNS:
            if col not in self.headers:

                new_col = len(self.headers) + 1
                self.sheet.update_cell(1, new_col, col)

                self.headers.append(col)
                self.col_index[col] = new_col

    # -------------------------------------------------
    def get_all_groups(self):
        return self.records

    # =================================================
    # JOIN STATUS LOGIC
    # =================================================

    def mark_joined(self, group_link):
        self._write_status(group_link, JoinStatus.YES)

    def mark_duplicate(self, group_link):
        self._write_status(group_link, JoinStatus.DUPLICATE)

    def mark_join_failed(self, group_link, reason):

        reason = str(reason).lower()

        if "expired" in reason:
            value = JoinStatus.EXPIRED

        elif "username" in reason or "nobody is using" in reason:
            value = JoinStatus.INVALID

        elif "entity" in reason:
            value = JoinStatus.PREVIEW

        elif "flood" in reason:
            value = JoinStatus.RETRY

        else:
            value = JoinStatus.FAILED

        self._write_status(group_link, value)

    def _write_status(self, group_link, value):
        row = self.row_map.get(group_link)
        if not row:
            print(f"Sheet row not found for {group_link}")
            return

        col = self.col_index.get("Telegram channel Joined ?")
        if not col:
            return

        self.sheet.update_cell(row, col, value)

    # =================================================
    # STATE MIRROR SYNC (DISPLAY ONLY)
    # =================================================

    def sync_group_state(self, group_link, data, total_processed):

        row = self.row_map.get(group_link)
        if not row:
            return

        self.sheet.update_cell(
            row,
            self.col_index["last_scanned_message_id"],
            str(data.get("last_scanned_id", 0))
        )

        self.sheet.update_cell(
            row,
            self.col_index["last_scanned_time"],
            data.get("last_scanned_time", "")
        )

        self.sheet.update_cell(
            row,
            self.col_index["total_resumes_fetched"],
            str(data.get("total_resumes", 0))
        )
        self.sheet.update_cell(
            row,
            self.col_index["total_processed"],
            str(total_processed)
        )