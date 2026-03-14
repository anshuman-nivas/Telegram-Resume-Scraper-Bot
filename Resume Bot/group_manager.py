# group_manager.py

import asyncio
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.errors import FloodWaitError
from utils import normalize_telegram_link, JoinStatus
from logger import logger

class GroupManager:

    def __init__(self, client):
        self.client = client
        self.entities = []
        self.group_link_map = {}
        self.group_title_map = {}

    # -------------------------------------------------
    # ENTITY RESOLUTION WITH RETRY
    # -------------------------------------------------
    async def _resolve_entity_with_retry(self, group_link,
                                         retries=2,
                                         delay=2):

        last_error = None

        for attempt in range(retries + 1):
            try:
                return await self.client.get_entity(group_link)

            except Exception as e:
                last_error = e

                if attempt < retries:
                    wait_time = delay * (attempt + 1)
                    logger.info(
                        f"Entity resolve retry {attempt+1} "
                        f"for {group_link} in {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)

        raise last_error

    # -------------------------------------------------
    # JOIN GROUPS
    # -------------------------------------------------
    async def join_groups(self, group_rows, sheets_manager=None):

        logger.info(f"\nJoining {len(group_rows)} groups...\n")

        for group in group_rows:

            raw_link = group.get("Telegram Link")
            group_link = normalize_telegram_link(raw_link)

            if not group_link:
                continue

            status = str(
                group.get("Telegram channel Joined ?", "")
            ).strip().lower()

            already_joined = status == JoinStatus.YES

            try:
                # =============================================
                # PRIVATE INVITE LINKS (t.me/+xxxx)
                # =============================================
                if "t.me/+" in group_link:

                    invite_hash = group_link.split("+")[-1]

                    if not already_joined:
                        try:
                            await self.client(
                                ImportChatInviteRequest(invite_hash)
                            )

                            if sheets_manager:
                                sheets_manager.mark_joined(group_link)

                        except Exception as e:
                            logger.info(f"Invite join attempt: {e}")

                            if sheets_manager:
                                sheets_manager.mark_join_failed(
                                    group_link, e)

                    entity = await self._resolve_entity_with_retry(
                        group_link
                    )

                # =============================================
                # PUBLIC CHANNELS
                # =============================================
                else:

                    entity = await self._resolve_entity_with_retry(
                        group_link
                    )

                    if not already_joined:
                        try:
                            await self.client(
                                JoinChannelRequest(entity)
                            )

                            if sheets_manager:
                                sheets_manager.mark_joined(group_link)

                        except Exception as e:
                            logger.info(f"Join attempt: {e}")

                            if sheets_manager:
                                sheets_manager.mark_join_failed(
                                    group_link, e)

                # =============================================
                # DUPLICATE SAFE ENTITY REGISTRATION
                # =============================================
                title = getattr(entity, "title", str(entity.id))

                if entity.id not in self.group_link_map:

                    self.entities.append(entity)
                    self.group_link_map[entity.id] = group_link
                    self.group_title_map[group_link] = title

                    logger.info(f"Monitoring: {title}")

                else:
                    logger.info(f"Duplicate group skipped: {title}")

                    if sheets_manager:
                        sheets_manager.mark_duplicate(group_link)

            # =============================================
            # FLOOD WAIT HANDLING
            # =============================================
            except FloodWaitError as e:

                wait_time = int(e.seconds)

                logger.info(f"FloodWait ({wait_time}s)... sleeping")

                await asyncio.sleep(wait_time + 5)

                if sheets_manager:
                    sheets_manager.mark_join_failed(
                        group_link,
                        JoinStatus.RETRY
                    )

            # =============================================
            # GENERAL FAILURE
            # =============================================
            except Exception as e:

                logger.info(f"Failed {group_link}: {e}")

                if sheets_manager:
                    sheets_manager.mark_join_failed(
                        group_link, e)