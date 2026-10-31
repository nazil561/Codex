import asyncio

import pytest


@pytest.mark.asyncio
async def test_schema_models_import():
    from live_engagement_coach.db import models
    from live_engagement_coach.db.base import Base

    assert Base.metadata.tables
