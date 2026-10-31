def test_health():
    from fastapi.testclient import TestClient
    from live_engagement_coach.main import app

    client = TestClient(app)
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
