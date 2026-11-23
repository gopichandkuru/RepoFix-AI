from auth.session import is_token_expired


def test_token_is_not_expired_before_ttl():
    assert is_token_expired(issued_at=1000, ttl_seconds=60, now=1030) is False
