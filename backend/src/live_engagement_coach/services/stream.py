from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from live_engagement_coach.db.models import StreamSnapshot, TwitchAccount
from live_engagement_coach.twitch.client import HelixClient


async def get_stream_fresh(session: AsyncSession, acc: TwitchAccount):
    # check last snapshot within 15s
    res = await session.execute(select(StreamSnapshot).where(StreamSnapshot.twitch_account_id == acc.id).order_by(desc(StreamSnapshot.captured_at)).limit(1))
    snap = res.scalar_one_or_none()
    if snap and (datetime.now(timezone.utc) - snap.captured_at.replace(tzinfo=timezone.utc) if snap.captured_at.tzinfo is None else datetime.now(timezone.utc) - snap.captured_at).total_seconds() < 15:
        return {
            "is_live": snap.is_live,
            "twitch_stream_id": snap.twitch_stream_id,
            "title": snap.title,
            "game_name": snap.game_name,
            "viewer_count": snap.viewer_count,
            "started_at": snap.started_at.isoformat().replace("+00:00", "Z") if snap.started_at else None,
            "captured_at": snap.captured_at.isoformat().replace("+00:00", "Z"),
            "freshness": "live",
        }
    # try refresh
    try:
        client = HelixClient(acc, session)
        data = await client.get_streams(acc.twitch_user_id)
        streams = data.get("data", [])
        if streams:
            s = streams[0]
            ns = StreamSnapshot(twitch_account_id=acc.id, twitch_stream_id=s.get("id"), title=s.get("title"), game_id=s.get("game_id"), game_name=s.get("game_name"), viewer_count=s.get("viewer_count"), started_at=None, is_live=True)
            session.add(ns)
            await session.commit()
            await session.refresh(ns)
            return {
                "is_live": True,
                "twitch_stream_id": ns.twitch_stream_id,
                "title": ns.title,
                "game_name": ns.game_name,
                "viewer_count": ns.viewer_count,
                "started_at": s.get("started_at"),
                "captured_at": ns.captured_at.isoformat().replace("+00:00", "Z"),
                "freshness": "live",
            }
        else:
            ns = StreamSnapshot(twitch_account_id=acc.id, twitch_stream_id=None, title=None, game_id=None, game_name=None, viewer_count=None, started_at=None, is_live=False)
            session.add(ns)
            await session.commit()
            await session.refresh(ns)
            return {
                "is_live": False,
                "twitch_stream_id": None,
                "title": None,
                "game_name": None,
                "viewer_count": None,
                "started_at": None,
                "captured_at": ns.captured_at.isoformat().replace("+00:00", "Z"),
                "freshness": "live",
            }
    except Exception:
        if snap:
            return {
                "is_live": snap.is_live,
                "twitch_stream_id": snap.twitch_stream_id,
                "title": snap.title,
                "game_name": snap.game_name,
                "viewer_count": snap.viewer_count,
                "started_at": snap.started_at.isoformat().replace("+00:00", "Z") if snap.started_at else None,
                "captured_at": snap.captured_at.isoformat().replace("+00:00", "Z"),
                "freshness": "stale",
                "warning": "twitch_unavailable",
            }
        raise
