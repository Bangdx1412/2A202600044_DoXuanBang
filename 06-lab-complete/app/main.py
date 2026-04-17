"""Production-ready AI agent for Day 12 final project."""
from __future__ import annotations

import json
import logging
import os
import signal
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from redis.exceptions import RedisError
import uvicorn

from app.auth import verify_api_key
from app.config import get_redis_client, settings
from app.cost_guard import (
    check_budget,
    estimate_cost,
    estimate_tokens,
    get_budget_status,
    record_cost,
)
from app.rate_limiter import check_rate_limit
from utils.mock_llm import ask as llm_ask


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(message)s",
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
INSTANCE_ID = os.getenv("RENDER_INSTANCE_ID") or os.getenv("HOSTNAME") or "local"
_is_ready = False
_redis_ready = False
_request_count = 0
_error_count = 0
_in_flight_requests = 0


def log_event(event: str, **fields) -> None:
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **fields,
    }
    logger.info(json.dumps(payload))


def _redis_ping() -> bool:
    try:
        get_redis_client().ping()
        return True
    except Exception:
        return False


def _history_key(user_id: str) -> str:
    return f"history:{user_id}"


def load_history(user_id: str) -> list[dict]:
    try:
        items = get_redis_client().lrange(_history_key(user_id), -settings.max_history_messages, -1)
    except RedisError as exc:
        raise HTTPException(status_code=503, detail="Redis unavailable") from exc
    return [json.loads(item) for item in items]


def append_history(user_id: str, role: str, content: str) -> None:
    entry = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        pipe = get_redis_client().pipeline()
        pipe.rpush(_history_key(user_id), json.dumps(entry))
        pipe.ltrim(_history_key(user_id), -settings.max_history_messages, -1)
        pipe.expire(_history_key(user_id), settings.history_ttl_seconds)
        pipe.execute()
    except RedisError as exc:
        raise HTTPException(status_code=503, detail="Redis unavailable") from exc


def delete_history(user_id: str) -> int:
    try:
        return int(get_redis_client().delete(_history_key(user_id)))
    except RedisError as exc:
        raise HTTPException(status_code=503, detail="Redis unavailable") from exc


@asynccontextmanager
async def lifespan(_: FastAPI):
    global _is_ready, _redis_ready

    log_event(
        "startup",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
    time.sleep(0.1)
    _redis_ready = _redis_ping()
    _is_ready = _redis_ready
    log_event("ready" if _is_ready else "not_ready", redis_connected=_redis_ready)

    yield

    _is_ready = False
    log_event("shutdown_started", in_flight_requests=_in_flight_requests)
    waited = 0
    while _in_flight_requests > 0 and waited < settings.graceful_shutdown_timeout_seconds:
        time.sleep(1)
        waited += 1
        log_event("shutdown_wait", in_flight_requests=_in_flight_requests, waited_seconds=waited)
    log_event("shutdown_complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global _request_count, _error_count, _in_flight_requests

    start = time.time()
    _request_count += 1
    _in_flight_requests += 1
    try:
        response: Response = await call_next(request)
    except Exception:
        _error_count += 1
        log_event("request_error", method=request.method, path=request.url.path)
        raise
    finally:
        _in_flight_requests -= 1

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"

    duration_ms = round((time.time() - start) * 1000, 1)
    log_event(
        "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=duration_ms,
    )
    return response


class AskRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    question: str = Field(..., min_length=1, max_length=2000)


class AskResponse(BaseModel):
    user_id: str
    question: str
    answer: str
    model: str
    history_messages: int
    budget_remaining_usd: float
    served_by: str
    timestamp: str


@app.get("/", tags=["Info"])
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "instance_id": INSTANCE_ID,
        "endpoints": {
            "ask": "POST /ask",
            "history": "GET /history/{user_id}",
            "health": "GET /health",
            "ready": "GET /ready",
        },
    }


@app.post("/ask", response_model=AskResponse, tags=["Agent"])
async def ask_agent(
    body: AskRequest,
    request: Request,
    _: str = Depends(verify_api_key),
):
    global _redis_ready, _is_ready

    _redis_ready = _redis_ping()
    _is_ready = _redis_ready
    if not _is_ready:
        raise HTTPException(status_code=503, detail="Service not ready. Redis unavailable.")

    check_rate_limit(body.user_id)

    input_tokens = estimate_tokens(body.question)
    estimated_total_cost = estimate_cost(input_tokens=input_tokens, output_tokens=max(32, input_tokens))
    check_budget(body.user_id, estimated_total_cost)

    prior_history = load_history(body.user_id)
    append_history(body.user_id, "user", body.question)

    log_event(
        "agent_call",
        user_id=body.user_id,
        history_messages=len(prior_history),
        client=request.client.host if request.client else "unknown",
    )

    answer = llm_ask(body.question)
    append_history(body.user_id, "assistant", answer)

    output_tokens = estimate_tokens(answer)
    actual_cost = estimate_cost(input_tokens=input_tokens, output_tokens=output_tokens)
    record_cost(body.user_id, actual_cost)

    history = load_history(body.user_id)
    budget = get_budget_status(body.user_id)

    return AskResponse(
        user_id=body.user_id,
        question=body.question,
        answer=answer,
        model=settings.llm_model,
        history_messages=len(history),
        budget_remaining_usd=budget["remaining_usd"],
        served_by=INSTANCE_ID,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/history/{user_id}", tags=["Agent"])
def get_history(user_id: str, _: str = Depends(verify_api_key)):
    history = load_history(user_id)
    return {"user_id": user_id, "messages": history, "count": len(history)}


@app.delete("/history/{user_id}", tags=["Agent"])
def clear_history(user_id: str, _: str = Depends(verify_api_key)):
    deleted = delete_history(user_id)
    return {"user_id": user_id, "deleted": deleted > 0}


@app.get("/health", tags=["Operations"])
def health():
    global _redis_ready
    _redis_ready = _redis_ping()
    return {
        "status": "ok" if _redis_ready else "degraded",
        "version": settings.app_version,
        "environment": settings.environment,
        "instance_id": INSTANCE_ID,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "redis_connected": _redis_ready,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready", tags=["Operations"])
def ready():
    global _redis_ready, _is_ready
    _redis_ready = _redis_ping()
    _is_ready = _redis_ready
    if not _is_ready:
        raise HTTPException(status_code=503, detail="Not ready. Redis unavailable.")
    return {"ready": True, "instance_id": INSTANCE_ID}


@app.get("/metrics", tags=["Operations"])
def metrics(_: str = Depends(verify_api_key)):
    return {
        "instance_id": INSTANCE_ID,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "error_count": _error_count,
        "redis_connected": _redis_ready,
    }


def _handle_signal(signum, _frame):
    log_event("signal_received", signum=signum)


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


if __name__ == "__main__":
    log_event("server_start", host=settings.host, port=settings.port)
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=settings.graceful_shutdown_timeout_seconds,
    )
