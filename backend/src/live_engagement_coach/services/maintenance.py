import asyncio
from datetime import datetime, timezone

from sqlalchemy import select, update

from live_engagement_coach.db.models import AppSession, TwitchAccount
from live_engagement_coach.db.session import AsyncSessionLocal
from live_engagement_coach.twitch.client import HelixClient


async def validate_all_tokens():
    while True:
        try:
            # Check every 30 minutes instead of 1 hour for better responsiveness
            await asyncio.sleep(1800)
            async with AsyncSessionLocal() as db:
                res = await db.execute(select(TwitchAccount).where(TwitchAccount.status == "connected"))
                for acc in res.scalars():
                    try:
                        # Proactive refresh check: if token expires within 15 mins, refresh now
                        from datetime import datetime, timezone, timedelta
                        if acc.token_expires_at and acc.token_expires_at < datetime.now(timezone.utc) + timedelta(minutes=15):
                            import logging
                            logger = logging.getLogger("maintenance")
                            logger.info(f"Token for {acc.login} is expiring soon. Proactively refreshing...")
                            from live_engagement_coach.twitch.client import HelixClient
                            hc = HelixClient(acc, db)
                            # Trigger a dummy request to force refresh via HelixClient._request logic
                            await hc.validate() 
                        else:
                            # Just validate if not expiring soon
                            from live_engagement_coach.twitch.client import HelixClient
                            hc = HelixClient(acc, db)
                            await hc.validate()
                    except Exception as e:
                        import logging
                        logging.getLogger("maintenance").error(f"Token validation failed for {acc.login}: {e}")
                        await db.execute(update(TwitchAccount).where(TwitchAccount.id == acc.id).values(status="needs_reauth"))
                        await db.execute(update(AppSession).where(AppSession.twitch_account_id == acc.id).values(expires_at=datetime.now(timezone.utc)))
                        await db.commit()
                        continue
        except Exception as e:
            import logging
            logging.getLogger("maintenance").error(f"Maintenance loop error: {e}")
            await asyncio.sleep(60)
            continue
