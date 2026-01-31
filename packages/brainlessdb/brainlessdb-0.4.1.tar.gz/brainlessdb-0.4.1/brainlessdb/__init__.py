"""Brainless DB - Typed collections backed by NATS JetStream KV."""

from typing import Any, Optional, TypeVar

from .client import BrainlessDB
from .collection import Collection, HasUUID
from .struct import BrainlessDBFeat, BrainlessStruct, UniqueConstraintError

__all__ = [
    "BrainlessDB",
    "BrainlessDBFeat",
    "BrainlessStruct",
    "Collection",
    "HasUUID",
    "UniqueConstraintError",
    "collection",
    "flush",
    "setup",
    "start",
    "stop",
]

T = TypeVar("T", bound=HasUUID)
_db: Optional[BrainlessDB] = None


def setup(nats: Any = None, namespace: str = "default", flush_interval: float = 0.5) -> BrainlessDB:
    """Initialize global instance."""
    global _db
    _db = BrainlessDB(nats, namespace, flush_interval)
    return _db


async def start() -> None:
    """Start global instance and load collections."""
    if not _db:
        raise RuntimeError("Call brainlessdb.setup() first")
    await _db.start()


async def stop() -> None:
    """Stop global instance."""
    global _db
    if _db:
        await _db.stop()
        _db = None


async def flush() -> int:
    """Flush all dirty entities."""
    if not _db:
        raise RuntimeError("Call brainlessdb.setup() first")
    return await _db.flush()


def collection(cls: type[T]) -> Collection[T]:
    """Get typed collection from global instance."""
    if not _db:
        raise RuntimeError("Call brainlessdb.setup() first")
    return _db.collection(cls)
