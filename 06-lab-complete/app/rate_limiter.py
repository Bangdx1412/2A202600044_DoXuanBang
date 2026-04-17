"""Redis-backed rate limiting."""
from __future__ import annotations

import time
import uuid

from fastapi import HTTPException
from redis.exceptions import RedisError

from app.config import get_redis_client, settings


WINDOW_SECONDS = 60


def check_rate_limit(user_id: str) -> None:
    client = get_redis_client()
    now = time.time()
    key = f"rate:{user_id}"
    member = f"{now}:{uuid.uuid4().hex}"

    try:
        pipe = client.pipeline()
        pipe.zremrangebyscore(key, 0, now - WINDOW_SECONDS)
        pipe.zcard(key)
        pipe.zadd(key, {member: now})
        pipe.expire(key, WINDOW_SECONDS + 5)
        _, current_count, _, _ = pipe.execute()
    except RedisError as exc:
        raise HTTPException(status_code=503, detail="Rate limiter unavailable.") from exc

    if current_count >= settings.rate_limit_per_minute:
        client.zrem(key, member)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": settings.rate_limit_per_minute,
                "window_seconds": WINDOW_SECONDS,
            },
            headers={"Retry-After": str(WINDOW_SECONDS)},
        )
