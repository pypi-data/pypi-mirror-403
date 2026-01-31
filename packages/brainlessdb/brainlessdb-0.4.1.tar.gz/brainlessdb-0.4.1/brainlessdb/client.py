"""Brainless DB main client."""

import asyncio
import logging
from typing import Any, Optional, TypeVar

from .bucket import Bucket
from .collection import Collection, HasUUID

_log = logging.getLogger(__name__)
T = TypeVar("T", bound=HasUUID)


class BrainlessDB:
    """Typed collections backed by NATS JetStream KV."""

    def __init__(self, nats: Any = None, namespace: str = "default", flush_interval: float = 0.1):
        self._nats = nats
        self._namespace = namespace
        self._flush_interval = flush_interval
        self._collections: dict[str, Collection] = {}
        self._js: Any = None
        self._flush_task: Optional[asyncio.Task] = None
        self._flush_pending = False
        self._flushing = False

    @property
    def namespace(self) -> str:
        return self._namespace

    @property
    def connected(self) -> bool:
        return self._js is not None

    async def get_bucket(self, name: str) -> Optional[Bucket]:
        if not self.connected:
            return None
        return await Bucket.create(self._js, name)

    def collection(self, cls: type[T]) -> Collection[T]:
        """Get or create collection.

        Collection is loaded when start() is called. If collection is
        registered after start(), call await collection.load() manually.
        """
        name = cls.__name__.lower()
        if name not in self._collections:
            self._collections[name] = Collection(self, cls)
        return self._collections[name]

    # === Flush scheduling ===

    def schedule_flush(self) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return

        if self._flush_task is not None:
            if self._flushing:
                self._flush_pending = True
            return

        if self._flush_interval == 0:
            self._flush_task = loop.create_task(self._do_flush())
        else:
            self._flush_task = loop.create_task(self._delayed_flush())

    async def _delayed_flush(self) -> None:
        await asyncio.sleep(self._flush_interval)
        await self._do_flush()

    async def _do_flush(self) -> None:
        self._flushing = True
        try:
            await self.flush()
        finally:
            self._flushing = False
            self._flush_task = None
            if self._flush_pending:
                self._flush_pending = False
                self.schedule_flush()

    async def flush(self) -> int:
        total = 0
        for coll in self._collections.values():
            total += await coll.flush()
        return total

    # === Watch ===

    async def watch(self) -> None:
        for coll in self._collections.values():
            await coll.watch()

    async def unwatch(self) -> None:
        for coll in self._collections.values():
            await coll.unwatch()

    # === Lifecycle ===

    async def start(self) -> None:
        if self._nats is not None:
            self._js = self._nats.jetstream()
        for coll in self._collections.values():
            await coll.load()
        _log.info("BrainlessDB started (namespace=%s)", self._namespace)

    async def stop(self) -> None:
        await self.unwatch()
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
            self._flush_task = None
        await self.flush()
        _log.info("BrainlessDB stopped")
