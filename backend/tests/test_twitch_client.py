import httpx
import respx


def test_twitch_client_refresh(monkeypatch):
    from live_engagement_coach.twitch import client
    # just import test
    assert client.HelixClient
