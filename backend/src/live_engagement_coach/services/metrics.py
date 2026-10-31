from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from live_engagement_coach.db.models import EngagementBucket, StreamSnapshot, TwitchAccount


async def get_metrics(session: AsyncSession, acc: TwitchAccount, window_minutes: int = 15):
    if window_minutes < 1 or window_minutes > 180:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail={"error": {"code": "invalid_window", "message": "Invalid window"}})
    now = datetime.now(timezone.utc)
    window_started = now - timedelta(minutes=window_minutes)
    res = await session.execute(
        select(func.coalesce(func.sum(EngagementBucket.chat_message_count), 0))
        .where(EngagementBucket.twitch_account_id == acc.id, EngagementBucket.bucket_start >= window_started)
    )
    chat_messages = res.scalar() or 0
    # unique chatters
    from live_engagement_coach.db.models import ChatterPresence

    res = await session.execute(
        select(func.count(func.distinct(ChatterPresence.chatter_hash)))
        .join(EngagementBucket)
        .where(EngagementBucket.twitch_account_id == acc.id, EngagementBucket.bucket_start >= window_started)
    )
    unique_chatters = res.scalar() or 0
    # latest viewer
    res = await session.execute(select(StreamSnapshot).where(StreamSnapshot.twitch_account_id == acc.id).order_by(desc(StreamSnapshot.captured_at)).limit(1))
    snap = res.scalar_one_or_none()
    latest_viewer = snap.viewer_count if snap and snap.viewer_count is not None else None
    ratio = (unique_chatters / latest_viewer) if latest_viewer and latest_viewer > 0 else None
    mpm = chat_messages / window_minutes if window_minutes > 0 else 0
    # last message
    res = await session.execute(select(func.max(EngagementBucket.bucket_start)).where(EngagementBucket.twitch_account_id == acc.id))
    last = res.scalar()
    mins_since = int((now - last).total_seconds() // 60) if last else window_minutes
    return {
        "window_minutes": window_minutes,
        "window_started_at": window_started.isoformat().replace("+00:00", "Z"),
        "window_ended_at": now.isoformat().replace("+00:00", "Z"),
        "chat_messages": int(chat_messages),
        "unique_chatters": int(unique_chatters),
        "messages_per_minute": round(float(mpm), 2),
        "latest_viewer_count": latest_viewer,
        "chat_participation_ratio": round(float(ratio), 2) if ratio is not None else None,
        "chat_participation_ratio_meaning": "unique chatters divided by the latest sampled viewer count; not retention or churn",
        "minutes_since_last_message": mins_since,
        "is_live": snap.is_live if snap else False,
        "event_gap": False,
    }
