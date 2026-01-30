"""Disk-backed cache powered by SQLite."""

from __future__ import annotations

import asyncio
import sqlite3
import time
from pathlib import Path
from typing import Any, Mapping

from pydantic import Field, ValidationError

from accuralai_core.contracts.errors import CacheError
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse

from .base import BaseCache, CacheConfig, extract_options


class DiskCacheOptions(CacheConfig):
    """Configuration settings for the SQLite cache."""

    path: str = Field(default=".cache/accuralai.sqlite")
    size_limit_mb: int | None = Field(default=None, ge=1)
    vacuum_on_start: bool = False
    ensure_directory: bool = True


class DiskCache(BaseCache):
    """SQLite-backed cache storing serialized responses."""

    def __init__(self, *, options: DiskCacheOptions | None = None) -> None:
        super().__init__(options=options)
        self.options: DiskCacheOptions = options or DiskCacheOptions()
        self._db_path = Path(self.options.path).expanduser()
        if self.options.ensure_directory:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS cache ("
            "cache_key TEXT PRIMARY KEY,"
            "payload TEXT NOT NULL,"
            "expires_at REAL,"
            "updated_at REAL NOT NULL"
            ")"
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at)")
        self._conn.commit()

        if self.options.vacuum_on_start:
            self._conn.execute("VACUUM")
            self._conn.commit()

    def __del__(self) -> None:  # pragma: no cover - destructor best effort
        try:
            self._conn.close()
        except Exception:
            pass

    async def get(self, key: str, *, request: GenerateRequest) -> GenerateResponse | None:
        async with self._lock:
            return await asyncio.to_thread(self._get_sync, key)

    async def set(self, key: str, value: GenerateResponse, *, ttl_s: int | None = None) -> None:
        expires_at = self._compute_expiry(ttl_s)
        payload = value.model_dump_json()
        async with self._lock:
            await asyncio.to_thread(self._set_sync, key, payload, expires_at)

    async def invalidate(self, key: str) -> None:
        async with self._lock:
            await asyncio.to_thread(self._invalidate_sync, key)

    async def invalidate_prefix(self, prefix: str) -> None:
        async with self._lock:
            await asyncio.to_thread(self._invalidate_prefix_sync, prefix)

    # Synchronous helpers executed inside a thread
    def _get_sync(self, key: str) -> GenerateResponse | None:
        self._remove_expired_sync()
        cursor = self._conn.execute(
            "SELECT payload, expires_at FROM cache WHERE cache_key = ?", (key,)
        )
        row = cursor.fetchone()
        if row is None:
            self._mark_miss()
            return None

        payload, expires_at = row
        if expires_at is not None and expires_at <= time.time():
            self._conn.execute("DELETE FROM cache WHERE cache_key = ?", (key,))
            self._conn.commit()
            self._mark_miss()
            return None

        self._conn.execute(
            "UPDATE cache SET updated_at = ? WHERE cache_key = ?", (time.time(), key)
        )
        self._conn.commit()
        self._mark_hit()
        return GenerateResponse.model_validate_json(payload).model_copy(deep=True)

    def _set_sync(self, key: str, payload: str, expires_at: float | None) -> None:
        now = time.time()
        self._conn.execute(
            "REPLACE INTO cache(cache_key, payload, expires_at, updated_at) "
            "VALUES (?, ?, ?, ?)",
            (key, payload, expires_at, now),
        )
        self._conn.commit()
        self._remove_expired_sync()
        self._enforce_size_limit_sync()

    def _invalidate_sync(self, key: str) -> None:
        self._conn.execute("DELETE FROM cache WHERE cache_key = ?", (key,))
        self._conn.commit()

    def _invalidate_prefix_sync(self, prefix: str) -> None:
        pattern = f"{prefix}%"
        self._conn.execute("DELETE FROM cache WHERE cache_key LIKE ?", (pattern,))
        self._conn.commit()

    def _remove_expired_sync(self) -> None:
        current = time.time()
        self._conn.execute("DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at <= ?", (current,))
        self._conn.commit()

    def _enforce_size_limit_sync(self) -> None:
        limit = self.options.size_limit_mb
        if limit is None:
            return
        byte_limit = limit * 1024 * 1024
        try:
            while self._db_path.exists() and self._db_path.stat().st_size > byte_limit:
                oldest = self._conn.execute(
                    "SELECT cache_key FROM cache ORDER BY updated_at ASC LIMIT 1"
                ).fetchone()
                if oldest is None:
                    break
                (key,) = oldest
                self._conn.execute("DELETE FROM cache WHERE cache_key = ?", (key,))
                self._conn.commit()
        except FileNotFoundError:
            # File removed while pruning; safe to ignore
            return


async def build_disk_cache(
    *,
    config: Mapping[str, Any] | Any | None = None,
    **_: Any,
) -> DiskCache:
    """Factory for the SQLite-backed disk cache."""
    try:
        options, _ = extract_options(config=config, options_model=DiskCacheOptions)
    except ValidationError as error:
        raise CacheError(f"Invalid disk cache options: {error}") from error

    return DiskCache(options=options)
