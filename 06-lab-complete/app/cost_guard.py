"""Redis-backed monthly budget control."""
from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from redis.exceptions import RedisError

from app.config import get_redis_client, settings


INPUT_PRICE_PER_1K = 0.00015
OUTPUT_PRICE_PER_1K = 0.0006
MONTH_TTL_SECONDS = 35 * 24 * 3600


def _month_key() -> str:
    return datetime.utcnow().strftime("%Y-%m")


def _budget_key(user_id: str) -> str:
    return f"budget:{user_id}:{_month_key()}"


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()) * 2)


def estimate_cost(input_tokens: int = 0, output_tokens: int = 0) -> float:
    input_cost = (input_tokens / 1000) * INPUT_PRICE_PER_1K
    output_cost = (output_tokens / 1000) * OUTPUT_PRICE_PER_1K
    return round(input_cost + output_cost, 6)


def _get_current_spend(user_id: str) -> float:
    client = get_redis_client()
    try:
        return float(client.get(_budget_key(user_id)) or 0.0)
    except RedisError as exc:
        raise HTTPException(status_code=503, detail="Budget store unavailable.") from exc


def check_budget(user_id: str, estimated_cost: float) -> None:
    current_spend = _get_current_spend(user_id)
    if current_spend + estimated_cost > settings.monthly_budget_usd:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Monthly budget exceeded",
                "budget_usd": settings.monthly_budget_usd,
                "used_usd": round(current_spend, 6),
                "estimated_cost_usd": round(estimated_cost, 6),
            },
        )


def record_cost(user_id: str, cost_usd: float) -> None:
    client = get_redis_client()
    try:
        pipe = client.pipeline()
        pipe.incrbyfloat(_budget_key(user_id), float(cost_usd))
        pipe.expire(_budget_key(user_id), MONTH_TTL_SECONDS)
        pipe.execute()
    except RedisError as exc:
        raise HTTPException(status_code=503, detail="Budget store unavailable.") from exc


def get_budget_status(user_id: str) -> dict:
    current_spend = _get_current_spend(user_id)
    remaining = max(0.0, settings.monthly_budget_usd - current_spend)
    used_pct = round((current_spend / settings.monthly_budget_usd) * 100, 1) if settings.monthly_budget_usd else 0
    return {
        "used_usd": round(current_spend, 6),
        "remaining_usd": round(remaining, 6),
        "budget_usd": settings.monthly_budget_usd,
        "used_pct": used_pct,
    }
