import asyncio
import json
import uuid
from datetime import datetime, timezone

import httpx
import websockets
from sqlalchemy import select, update

from live_engagement_coach.config import settings
from live_engagement_coach.db.models import ChatterPresence, EngagementBucket, EventReceipt, EventSubSubscription, ListeningSession
from live_engagement_coach.db.session import AsyncSessionLocal
from live_engagement_coach.security.sessions import hash_chatter_id
from live_engagement_coach.twitch.parsers import parse_chat_message


class EventSubListener:
    WS_URL = "wss://eventsub.wss.twitch.tv/ws"

    def __init__(self, account_id: uuid.UUID, twitch_user_id: str, access_token: str):
        self.account_id = account_id
        self.twitch_user_id = twitch_user_id
        self.access_token = access_token
        self.session_id = None
        self._current_ws_url = self.WS_URL
        self._buffer: dict[tuple[datetime, str], int] = {}  # (bucket_start, chatter_hash) -> count
        self._chat_counts: dict[datetime, int] = {}       # bucket_start -> total_count
        self._flush_task: asyncio.Task | None = None


    async def _update_session(self, **kwargs):
        try:
            async with AsyncSessionLocal() as db:
                await db.execute(update(ListeningSession).where(ListeningSession.twitch_account_id == self.account_id).values(**kwargs))
                await db.commit()
        except Exception:
            pass

    async def start(self):
        try:
            await self._update_session(status="connecting")
            while True:
                try:
                    async with websockets.connect(self._current_ws_url) as ws:
                        raw = await ws.recv()
                        msg = json.loads(raw)
                        if msg.get("metadata", {}).get("message_type") == "session_welcome":
                            self.session_id = msg["payload"]["session"]["id"]
                            await self._update_session(websocket_session_id=self.session_id, status="listening")
                        
                        async with AsyncSessionLocal() as db:
                            res = await db.execute(select(ListeningSession).where(ListeningSession.twitch_account_id == self.account_id).order_by(ListeningSession.started_at.desc()).limit(1))
                            ls = res.scalar_one_or_none()
                            if ls:
                                await self._subscribe(db, ls.id)
                            await db.commit()

                        # Start buffer flush task on first successful connection
                        if self._flush_task is None:
                            self._flush_task = asyncio.create_task(self._periodic_flush())

                        async for raw in ws:
                            msg = json.loads(raw)
                            mtype = msg.get("metadata", {}).get("message_type")
                            if mtype == "notification":
                                await self._handle_notification(msg)
                            elif mtype == "session_reconnect":
                                reconnect_info = msg["payload"]["reconnect"]
                                self._current_ws_url = reconnect_info["reconnect_url"]
                                await self._update_session(status="degraded", last_gap_at=datetime.now(timezone.utc))
                                break # Trigger reconnection loop
                            elif mtype == "revocation":
                                await self._update_session(status="degraded", last_gap_at=datetime.now(timezone.utc))
                                break
                except (websockets.ConnectionClosed, asyncio.TimeoutError):
                    await asyncio.sleep(5) # Backoff before reconnecting
                    continue
        except Exception:
            await self._update_session(status="degraded", last_gap_at=datetime.now(timezone.utc))
            raise
        finally:
            if self._flush_task:
                self._flush_task.cancel()

    async def _subscribe(self, db, ls_id):
        types = ["channel.chat.message", "channel.poll.begin", "channel.poll.progress", "channel.poll.end"]
        for t in types:
            if t == "channel.chat.message":
                condition = {"broadcaster_user_id": self.twitch_user_id, "user_id": self.twitch_user_id}
                version = "1"
            else:
                condition = {"broadcaster_user_id": self.twitch_user_id}
                version = "1"
            payload = {
                "type": t,
                "version": version,
                "condition": condition,
                "transport": {"method": "websocket", "session_id": self.session_id},
            }
            async with httpx.AsyncClient(timeout=10) as client:
                try:
                    resp = await client.post(
                        "https://api.twitch.tv/helix/eventsub/subscriptions",
                        json=payload,
                        headers={"Authorization": f"Bearer {self.access_token}", "Client-Id": settings.TWITCH_CLIENT_ID},
                    )
                    if resp.status_code == 202:
                        data = resp.json()
                        sub = data.get("data", [{}])[0]
                        db.add(EventSubSubscription(listening_session_id=ls_id, twitch_subscription_id=sub.get("id", ""), subscription_type=t, status="enabled"))
                except Exception:
                    continue

    async def _handle_notification(self, msg: dict):
        metadata = msg.get("metadata", {})
        message_id = metadata.get("message_id")
        if not message_id:
            return

        ev = msg.get("payload", {}).get("event", {})
        sub_type = metadata.get("subscription_type") or msg.get("payload", {}).get("subscription", {}).get("type") or ""
        
        if sub_type == "channel.chat.message":
            parsed = parse_chat_message(ev)
            bucket_start = parsed["bucket_start"]
            chatter_hash = hash_chatter_id(parsed["chatter_user_id"])
            self._chat_counts[bucket_start] = self._chat_counts.get(bucket_start, 0) + 1
            self._buffer[(bucket_start, chatter_hash)] = self._buffer.get((bucket_start, chatter_hash), 0) + 1
            async with AsyncSessionLocal() as db:
                res = await db.execute(select(EventReceipt).where(EventReceipt.message_id == message_id))
                if not res.scalar_one_or_none():
                    db.add(EventReceipt(message_id=message_id, twitch_account_id=self.account_id, subscription_type=sub_type, message_timestamp=parsed["timestamp"]))
                    await db.commit()
        else:
            async with AsyncSessionLocal() as db:
                res = await db.execute(select(EventReceipt).where(EventReceipt.message_id == message_id))
                if not res.scalar_one_or_none():
                    db.add(EventReceipt(message_id=message_id, twitch_account_id=self.account_id, subscription_type=sub_type, message_timestamp=datetime.now(timezone.utc)))
                    await db.commit()

        async with AsyncSessionLocal() as db:
            await db.execute(update(ListeningSession).where(ListeningSession.twitch_account_id == self.account_id).values(last_event_at=datetime.now(timezone.utc)))
            await db.commit()

    async def _periodic_flush(self):
        while True:
            try:
                await asyncio.sleep(5)
                if not self._chat_counts and not self._buffer:
                    continue
                async with AsyncSessionLocal() as db:
                    for bucket_start, count in self._chat_counts.items():
                        await db.execute(update(EngagementBucket).where(EngagementBucket.twitch_account_id == self.account_id, EngagementBucket.bucket_start == bucket_start).values(chat_message_count=EngagementBucket.chat_message_count + count))
                    for (bucket_start, chatter_hash), count in self._buffer.items():
                        res = await db.execute(select(EngagementBucket).where(EngagementBucket.twitch_account_id == self.account_id, EngagementBucket.bucket_start == bucket_start))
                        bucket = res.scalar_one_or_none()
                        if not bucket:
                            bucket = EngagementBucket(twitch_account_id=self.account_id, bucket_start=bucket_start, chat_message_count=0)
                            db.add(bucket)
                            await db.flush()
                        from sqlalchemy.dialects.postgresql import insert
                        stmt = insert(ChatterPresence).values(bucket_id=bucket.id, chatter_hash=chatter_hash).on_conflict_do_nothing()
                        await db.execute(stmt)
                    await db.commit()
                self._chat_counts.clear()
                self._buffer.clear()
            except Exception:
                continue
