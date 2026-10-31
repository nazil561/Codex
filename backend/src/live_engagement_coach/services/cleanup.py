import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from live_engagement_coach.db.models import ChatterPresence, EngagementBucket, EventReceipt
from live_engagement_coach.db.session import AsyncSessionLocal


async def start_cleanup_loop():
    while True:
        try:
            await asyncio.sleep(3600)
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            async with AsyncSessionLocal() as db:
                # delete old receipts
                await db.execute(delete(EventReceipt).where(EventReceipt.received_at < cutoff))
                # delete chatter presence for old buckets
                res = await db.execute(select(EngagementBucket.id).where(EngagementBucket.bucket_start < cutoff))
                ids = [r[0] for r in res.all()]
                if ids:
                    await db.execute(delete(ChatterPresence).where(ChatterPresence.bucket_id.in_(ids)))
                await db.commit()
        except Exception:
            await asyncio.sleep(60)
            continue
