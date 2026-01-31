"""Mock NATS for testing."""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class MockEntry:
    """Mock KV entry."""

    key: str
    value: Optional[bytes]
    revision: int
    operation: str = "PUT"


@dataclass
class MockKV:
    """Mock NATS KV bucket."""

    name: str
    _data: dict[str, bytes] = field(default_factory=dict)
    _revision: int = 0
    _watchers: list[asyncio.Queue] = field(default_factory=list)

    async def get(self, key: str) -> Optional[MockEntry]:
        if key not in self._data:
            raise KeyError(f"key {key} not found")
        return MockEntry(key=key, value=self._data[key], revision=self._revision)

    async def put(self, key: str, value: bytes) -> int:
        self._revision += 1
        self._data[key] = value
        entry = MockEntry(key=key, value=value, revision=self._revision)
        for q in self._watchers:
            await q.put(entry)
        return self._revision

    async def delete(self, key: str) -> None:
        self._revision += 1
        self._data.pop(key, None)
        entry = MockEntry(key=key, value=None, revision=self._revision, operation="DEL")
        for q in self._watchers:
            await q.put(entry)

    async def keys(self) -> list[str]:
        return list(self._data.keys())

    async def watchall(self, include_history: bool = False) -> "MockWatcher":
        q: asyncio.Queue = asyncio.Queue()
        self._watchers.append(q)
        return MockWatcher(q, self._watchers)


class MockWatcher:
    """Mock KV watcher."""

    def __init__(self, queue: asyncio.Queue, watchers: list):
        self._queue = queue
        self._watchers = watchers

    async def updates(self, timeout: Optional[float] = None) -> MockEntry:
        return await self._queue.get()

    async def stop(self) -> None:
        if self._queue in self._watchers:
            self._watchers.remove(self._queue)


class MockJetStream:
    """Mock NATS JetStream."""

    def __init__(self):
        self._buckets: dict[str, MockKV] = {}

    async def key_value(self, name: str) -> MockKV:
        if name not in self._buckets:
            from nats.js.errors import BucketNotFoundError
            raise BucketNotFoundError
        return self._buckets[name]

    async def create_key_value(self, config: Any) -> MockKV:
        name = config.bucket
        if name not in self._buckets:
            self._buckets[name] = MockKV(name=name)
        return self._buckets[name]


class MockNats:
    """Mock NATS client."""

    def __init__(self):
        self._js = MockJetStream()

    def jetstream(self) -> MockJetStream:
        return self._js
