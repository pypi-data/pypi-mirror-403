"""File-based JSON cache for human-readable storage."""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any, Mapping

from pydantic import Field, ValidationError

from accuralai_core.contracts.errors import CacheError
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse

from .base import BaseCache, CacheConfig, extract_options


class FileCacheOptions(CacheConfig):
    """Configuration settings for file-based cache."""

    directory: str = Field(default=".cache/accuralai-file")
    ensure_directory: bool = True
    max_files: int | None = Field(default=None, ge=1, description="Maximum number of cache files")
    file_extension: str = Field(default=".json")


class FileCache(BaseCache):
    """File-based cache storing JSON files."""

    def __init__(self, *, options: FileCacheOptions | None = None) -> None:
        super().__init__(options=options)
        self.options: FileCacheOptions = options or FileCacheOptions()
        self._cache_dir = Path(self.options.directory).expanduser()
        if self.options.ensure_directory:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _key_to_path(self, key: str) -> Path:
        """Convert cache key to file path."""
        # Sanitize key for filesystem
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self._cache_dir / f"{safe_key}{self.options.file_extension}"

    async def get(self, key: str, *, request: GenerateRequest) -> GenerateResponse | None:
        file_path = self._key_to_path(key)
        if not file_path.exists():
            self._mark_miss()
            return None

        try:
            async with self._lock:
                data = await asyncio.to_thread(self._read_file_sync, file_path)

            if data is None:
                self._mark_miss()
                return None

            payload, expires_at = data
            if expires_at is not None and expires_at <= time.time():
                await self.invalidate(key)
                self._mark_miss()
                return None

            response = GenerateResponse.model_validate(payload)
            self._mark_hit()
            return self._clone(response)
        except Exception:
            self._mark_miss()
            return None

    async def set(self, key: str, value: GenerateResponse, *, ttl_s: int | None = None) -> None:
        file_path = self._key_to_path(key)
        expires_at = self._compute_expiry(ttl_s)
        payload = value.model_dump()

        try:
            async with self._lock:
                await asyncio.to_thread(self._write_file_sync, file_path, payload, expires_at)
                await self._enforce_max_files()
        except Exception:
            pass  # Cache write failures are acceptable

    async def invalidate(self, key: str) -> None:
        file_path = self._key_to_path(key)
        try:
            async with self._lock:
                if file_path.exists():
                    await asyncio.to_thread(file_path.unlink)
        except Exception:
            pass

    async def invalidate_prefix(self, prefix: str) -> None:
        # Find all files matching prefix
        safe_prefix = prefix.replace("/", "_").replace("\\", "_")
        pattern = f"{safe_prefix}*{self.options.file_extension}"

        try:
            async with self._lock:
                files = list(self._cache_dir.glob(pattern))
                for file_path in files:
                    await asyncio.to_thread(file_path.unlink)
        except Exception:
            pass

    async def _enforce_max_files(self) -> None:
        """Enforce maximum number of files by removing oldest."""
        if self.options.max_files is None:
            return

        try:
            files = list(self._cache_dir.glob(f"*{self.options.file_extension}"))
            if len(files) <= self.options.max_files:
                return

            # Sort by modification time
            files.sort(key=lambda p: p.stat().st_mtime)

            # Remove oldest files
            to_remove = files[: len(files) - self.options.max_files]
            for file_path in to_remove:
                file_path.unlink()
        except Exception:
            pass

    def _read_file_sync(self, file_path: Path) -> tuple[dict[str, Any], float | None] | None:
        """Read cache file synchronously."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            payload = data.get("payload")
            expires_at = data.get("expires_at")
            return payload, expires_at
        except Exception:
            return None

    def _write_file_sync(self, file_path: Path, payload: dict[str, Any], expires_at: float | None) -> None:
        """Write cache file synchronously."""
        if self.options.ensure_directory:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        data = {"payload": payload, "expires_at": expires_at}
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


async def build_file_cache(
    *,
    config: Mapping[str, Any] | Any | None = None,
    **_: Any,
) -> FileCache:
    """Factory for file-based cache."""
    try:
        options, _ = extract_options(config=config, options_model=FileCacheOptions)
    except ValidationError as error:
        raise CacheError(f"Invalid file cache options: {error}") from error

    return FileCache(options=options)

