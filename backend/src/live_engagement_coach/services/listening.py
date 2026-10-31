import asyncio
import uuid

from sqlalchemy import select, update

from live_engagement_coach.db.models import ListeningSession, TwitchAccount
from live_engagement_coach.db.session import AsyncSessionLocal
from live_engagement_coach.security.crypto import decrypt_token
from live_engagement_coach.twitch.eventsub import EventSubListener


class ListenerManager:
    def __init__(self):
        self.tasks: dict[uuid.UUID, asyncio.Task] = {}

    async def start_listener(self, account_id: uuid.UUID):
        if account_id in self.tasks and not self.tasks[account_id].done():
            return
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(TwitchAccount).where(TwitchAccount.id == account_id))
            acc = res.scalar_one_or_none()
            if not acc:
                return
            try:
                token = decrypt_token(acc.access_token_ciphertext)
            except Exception:
                return
            # create session if not exists
            ls = ListeningSession(twitch_account_id=acc.id, status="connecting")
            db.add(ls)
            await db.execute(update(TwitchAccount).where(TwitchAccount.id == account_id).values(listening_desired=True))
            await db.commit()
        listener = EventSubListener(account_id, acc.twitch_user_id, token)
        task = asyncio.create_task(listener.start())
        self.tasks[account_id] = task

    async def stop_listener(self, account_id: uuid.UUID):
        task = self.tasks.get(account_id)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except Exception:
                pass
        self.tasks.pop(account_id, None)
        async with AsyncSessionLocal() as db:
            await db.execute(update(TwitchAccount).where(TwitchAccount.id == account_id).values(listening_desired=False))
            await db.execute(update(ListeningSession).where(ListeningSession.twitch_account_id == account_id).values(status="stopped", stopped_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc)))
            await db.commit()
        # if needs_reauth, ensure stopped
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(TwitchAccount).where(TwitchAccount.id == account_id))
            acc = res.scalar_one_or_none()
            if acc and acc.status == "needs_reauth":
                await db.execute(update(ListeningSession).where(ListeningSession.twitch_account_id == account_id).values(status="stopped"))
                await db.commit()

    async def stop_all(self):
        for aid in list(self.tasks.keys()):
            await self.stop_listener(aid)


async def start_snapshot_loop(manager: ListenerManager):
    while True:
        try:
            await asyncio.sleep(30)
            async with AsyncSessionLocal() as db:
                res = await db.execute(select(TwitchAccount).where(TwitchAccount.listening_desired == True, TwitchAccount.status == "connected"))
                for acc in res.scalars():
                    try:
                        from live_engagement_coach.twitch.client import HelixClient
                        hc = HelixClient(acc, db)
                        data = await hc.get_streams(acc.twitch_user_id)
                        streams = data.get("data", [])
                        from live_engagement_coach.db.models import StreamSnapshot
                        if streams:
                            s = streams[0]
                            db.add(StreamSnapshot(twitch_account_id=acc.id, twitch_stream_id=s.get("id"), title=s.get("title"), game_id=s.get("game_id"), game_name=s.get("game_name"), viewer_count=s.get("viewer_count"), started_at=None, is_live=True))
                        else:
                            db.add(StreamSnapshot(twitch_account_id=acc.id, twitch_stream_id=None, title=None, game_id=None, game_name=None, viewer_count=None, started_at=None, is_live=False))
                        await db.commit()
                    except Exception:
                        continue
        except Exception:
            await asyncio.sleep(5)
            continue
