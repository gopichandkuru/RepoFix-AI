def is_token_expired(issued_at: int, ttl_seconds: int, now: int) -> bool:
    expires_at = issued_at + ttl_seconds
    # Bug: inverted comparison treats non-expired tokens as expired
    return now < expires_at
