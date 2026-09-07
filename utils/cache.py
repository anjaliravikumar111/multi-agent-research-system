"""
Redis-based caching layer.
Avoids redundant Tavily / LLM API calls for repeated queries.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Optional

import redis

# ── connection ──────────────────────────────────────────────────────────────

def _make_client() -> redis.Redis:
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        password=os.getenv("REDIS_PASSWORD") or None,
        decode_responses=True,
        socket_connect_timeout=2,
    )


_client: Optional[redis.Redis] = None
_available: Optional[bool] = None


def _get_client() -> Optional[redis.Redis]:
    global _client, _available
    if _available is False:
        return None
    if _client is None:
        try:
            _client = _make_client()
            _client.ping()
            _available = True
        except Exception:
            _available = False
            _client = None
    return _client


# ── helpers ──────────────────────────────────────────────────────────────────

def _key(namespace: str, raw: str) -> str:
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"mars:{namespace}:{digest}"


TTL = int(os.getenv("CACHE_TTL_SECONDS", 3600))


# ── public API ───────────────────────────────────────────────────────────────

def get(namespace: str, query: str) -> Optional[Any]:
    """Return cached value or None."""
    client = _get_client()
    if client is None:
        return None
    try:
        raw = client.get(_key(namespace, query))
        return json.loads(raw) if raw else None
    except Exception:
        return None


def set(namespace: str, query: str, value: Any) -> None:  # noqa: A001
    """Cache value with TTL."""
    client = _get_client()
    if client is None:
        return
    try:
        client.setex(_key(namespace, query), TTL, json.dumps(value))
    except Exception:
        pass


def is_available() -> bool:
    return _get_client() is not None


def stats() -> dict:
    client = _get_client()
    if client is None:
        return {"status": "unavailable"}
    try:
        info = client.info("stats")
        return {
            "status": "connected",
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "keys": client.dbsize(),
        }
    except Exception as exc:
        return {"status": f"error: {exc}"}
