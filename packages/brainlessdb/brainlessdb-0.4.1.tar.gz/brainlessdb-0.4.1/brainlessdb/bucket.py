"""NATS JetStream KV bucket wrapper."""

import logging
from collections.abc import AsyncIterator
from typing import Any, Optional

from nats.js.api import KeyValueConfig
from nats.js.errors import BucketNotFoundError

_log = logging.getLogger(__name__)


class WatchEntry:
    """Entry from KV watch."""

    __slots__ = ("key", "value", "operation", "revision")

    def __init__(self, key: str, value: Optional[bytes], operation: str, revision: int):
        self.key = key
        self.value = value
        self.operation = operation
        self.revision = revision


class Bucket:
    """NATS JetStream KV bucket wrapper."""

    def __init__(self, kv: Any):
        self._kv = kv

    @classmethod
    async def create(cls, js: Any, name: str) -> "Bucket":
        """Create or get existing KV bucket."""
        try:
            kv = await js.key_value(name)
        except BucketNotFoundError:
            kv = await js.create_key_value(KeyValueConfig(bucket=name))
            _log.info("Created bucket: %s", name)
        return cls(kv)

    async def get(self, key: str) -> Optional[bytes]:
        try:
            entry = await self._kv.get(key)
            return entry.value if entry else None
        except Exception as e:
            if "not found" in str(e).lower():
                return None
            raise

    async def put(self, key: str, value: bytes) -> int:
        return await self._kv.put(key, value)

    async def delete(self, key: str) -> None:
        try:
            await self._kv.delete(key)
        except Exception as e:
            if "not found" not in str(e).lower():
                raise

    async def keys(self) -> list[str]:
        try:
            return await self._kv.keys()
        except Exception as e:
            if "no keys" in str(e).lower():
                return []
            raise

    async def all(self) -> dict[str, bytes]:
        result = {}
        for key in await self.keys():
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result

    async def watch(self, include_history: bool = False) -> AsyncIterator[WatchEntry]:
        watcher = await self._kv.watchall(include_history=include_history)
        try:
            while True:
                entry = await watcher.updates(timeout=None)
                if entry is None:
                    continue
                op = str(entry.operation) if entry.operation else ""
                is_del = "DEL" in op.upper() or "PURGE" in op.upper() or entry.value is None
                yield WatchEntry(entry.key, entry.value, "DEL" if is_del else "PUT", entry.revision)
        finally:
            await watcher.stop()
