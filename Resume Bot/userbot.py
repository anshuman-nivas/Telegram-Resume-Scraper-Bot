import os
import sys
import asyncio
import shutil

from telethon import TelegramClient, events

from config import *
from resume_processor import ResumeProcessor
from group_manager import GroupManager
from sheets_manager import SheetsManager
from state_manager import StateManager
from logger import logger


# -------------------------------------------------
# BASE DIR SAFE FOR EXE
# -------------------------------------------------
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
    os.chdir(BASE_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


TEMP_DIR = os.path.join(BASE_DIR, "temp")
RESUME_DIR = os.path.join(BASE_DIR, "resumes")


# -------------------------------------------------
# FOLDER INIT
# -------------------------------------------------
shutil.rmtree(TEMP_DIR, ignore_errors=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(RESUME_DIR, exist_ok=True)


# -------------------------------------------------
# UTF8 FIX (EXE SAFE)
# -------------------------------------------------
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except:
    pass


# -------------------------------------------------
# SHEET MIRROR WORKER
# -------------------------------------------------
async def sheet_sync_worker(state, sheets):

    while True:
        await asyncio.sleep(30)

        snapshot = state.snapshot()

        for group_link, data in snapshot.items():
            sheets.sync_group_state(
                group_link,
                data,
                state.get_total_processed()
            )

        logger.info("Sheet mirror synced")


# -------------------------------------------------
# MAIN
# -------------------------------------------------
async def main():

    sheets_manager = SheetsManager(
        GOOGLE_SHEETS_CREDENTIALS_PATH,
        GOOGLE_SHEETS_ID
    )

    state_manager = StateManager()

    resume_processor = ResumeProcessor(state_manager)

    session_path = os.path.join(BASE_DIR, "userbot_session")

    async with TelegramClient(
        session_path,
        API_ID,
        API_HASH
    ) as client:

        await client.start(phone=PHONE)

        logger.info("Telegram client started")

        asyncio.create_task(
            sheet_sync_worker(state_manager, sheets_manager)
        )

        group_manager = GroupManager(client)

        groups = list(reversed(
            sheets_manager.get_all_groups()
        ))

        await group_manager.join_groups(groups, sheets_manager)

        # ---------------- HISTORICAL ----------------
        for entity in group_manager.entities:

            group_link = group_manager.group_link_map.get(entity.id)

            if not group_link:
                continue

            last_id = state_manager.get_last_scanned(group_link)

            logger.info(
                f"Resuming scan for {group_link} "
                f"from message {last_id}"
            )

            async for msg in client.iter_messages(
                    entity,
                    min_id=last_id,
                    reverse=True):
                if msg.document or msg.photo:
                    processed = await resume_processor.process_document(
                        msg,
                        group_link,
                        group_manager.group_title_map
                    )
                    if processed:
                        state_manager.mark_message_seen(group_link, msg.id)
                else:
                    state_manager.mark_message_seen(group_link, msg.id)

        # ---------------- LIVE ----------------
        @client.on(events.NewMessage(chats=group_manager.entities))
        async def handler(event):

            group_link = group_manager.group_link_map.get(
                event.chat_id
            )

            if event.message.document or event.message.photo:

                processed = await resume_processor.process_document(
                    event.message,
                    group_link,
                    group_manager.group_title_map
                )

                if processed:
                    state_manager.mark_message_seen(
                        group_link,
                        event.message.id
                    )

            else:
                state_manager.mark_message_seen(
                    group_link,
                    event.message.id
        )


# -------------------------------------------------
# ENTRY
# -------------------------------------------------
if __name__ == "__main__":

    try:
        logger.info("BOT STARTING")
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("BOT STOPPED BY USER")

    except Exception:
        logger.exception("BOT CRASHED")