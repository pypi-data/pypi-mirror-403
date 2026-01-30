"""Handle httpx client and hishel caching."""

import contextlib
import logging
import os
from datetime import timedelta
from pathlib import Path
from typing import Final

import logfire
from hishel import FilterPolicy, SyncSqliteStorage
from hishel.httpx import SyncCacheClient

CACHE: Final = timedelta(minutes=5).total_seconds()
TIMEOUT: Final = timedelta(seconds=20).total_seconds()

logger = logging.getLogger(__name__)

logging.getLogger("httpcore").setLevel(logging.INFO)
# hishel DEBUG level is verbose about cached responses, use INFO instead
logging.getLogger("hishel").setLevel(logging.INFO)


def _cache_ttl_seconds() -> float:
    """Return cache TTL, allowing an env override for test runs."""
    if env_ttl := os.getenv("UNTAPPD_SCRAPER_CACHE_TTL_SECONDS"):
        with contextlib.suppress(ValueError):
            return float(env_ttl)
    return CACHE


def get_httpx_client() -> SyncCacheClient:
    """Return an HTTPX client with caching enabled.

    By default, uses in-memory cache (safe for production/FastAPI).
    In test environments, set UNTAPPD_SCRAPER_CACHE_DIR to enable
    persistent filesystem cache across test runs.
    """
    # Use filesystem cache only if explicitly enabled for testing
    if cache_dir := os.getenv("UNTAPPD_SCRAPER_CACHE_DIR"):
        # Test mode: persistent filesystem cache across test runs
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_db = cache_dir / "hishel_cache.db"

        storage = SyncSqliteStorage(
            database_path=str(cache_db),
            default_ttl=_cache_ttl_seconds(),
        )
        db_path = str(cache_db)
    else:
        # Default (production): in-memory cache (no filesystem writes)
        # Cache persists for the lifetime of the process
        storage = SyncSqliteStorage(
            database_path=":memory:",
            default_ttl=_cache_ttl_seconds(),
        )
        db_path = ":memory: (in-process only)"

    ttl = _cache_ttl_seconds()
    logger.debug("Initialized SyncSqliteStorage with TTL=%ss, path=%s", ttl, db_path)
    # Force caching even if origin sends no-cache/pragma headers.
    policy = FilterPolicy()
    logger.debug("Using FilterPolicy to force caching regardless of cache-control headers")

    cache_client = SyncCacheClient(
        follow_redirects=True,
        storage=storage,
        policy=policy,
        timeout=TIMEOUT,
        # Untappd / Cloudflare issues a JavaScript challenge for http1 requests only, perhaps
        http1=False,
        http2=True,
    )

    logger.info(
        "HTTPX client initialized: timeout=%ss, caching enabled, storage=%s", TIMEOUT, db_path
    )
    return cache_client


client = get_httpx_client()


if os.getenv("LOGFIRE_TOKEN"):
    logfire.instrument_httpx(client)
