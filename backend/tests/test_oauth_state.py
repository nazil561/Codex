import secrets

from cryptography.fernet import Fernet


def test_oauth_state():
    from live_engagement_coach.security.sessions import generate_state, hash_state
    s = generate_state()
    assert hash_state(s) != s
    h = hash_state(s)
    assert hash_state(s) == h
