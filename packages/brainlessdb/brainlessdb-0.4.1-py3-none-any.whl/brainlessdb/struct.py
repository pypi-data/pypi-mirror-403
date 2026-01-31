"""Structs for brainlessdb storage."""

import time
from enum import IntFlag, auto
from typing import Any
from uuid import UUID, uuid1
from weakref import WeakValueDictionary

from msgspec import Struct, field, convert, to_builtins


class BrainlessDBFeat(IntFlag):
    """Feature flags for field metadata."""

    INDEX = auto()
    STATE = auto()
    UNIQUE = auto()


class UniqueConstraintError(Exception):
    """Raised when a unique constraint is violated."""

    def __init__(self, field: str, value: Any) -> None:
        self.field = field
        self.value = value
        super().__init__(f"Unique constraint violated: {field}={value!r}")


# Registry: uuid -> collection (weak refs to avoid memory leaks)
_registry: WeakValueDictionary = WeakValueDictionary()


def _register(uuid: UUID, collection: Any) -> None:
    _registry[uuid] = collection


def _unregister(uuid: UUID) -> None:
    _registry.pop(uuid, None)


class BrainlessStruct(Struct, kw_only=True, tag=True, tag_field="TYPE"):
    """Base struct for brainlessdb entities."""

    _uuid: UUID = field(default_factory=uuid1)

    @property
    def uuid(self) -> UUID:
        return self._uuid

    def save(self) -> None:
        """Mark entity as dirty in its collection."""
        collection = _registry.get(self._uuid)
        if collection:
            collection.add(self)

    def update(self, data: dict) -> "BrainlessStruct":
        """Update fields from dict, supports nested structs."""
        for key, value in data.items():
            if not hasattr(self, key):
                continue
            if isinstance(value, dict):
                current = getattr(self, key)
                if current is not None and hasattr(current, "__struct_fields__"):
                    merged = {**to_builtins(current), **value}
                    value = convert(merged, type(current))
            setattr(self, key, value)
        self.save()
        return self


class Metadata(Struct):
    """Config bucket entry metadata."""

    created_at: float = 0.0
    updated_at: float = 0.0
    created_by: str = ""


class ConfigWrapper(Struct):
    """Wrapper for config bucket: {d: data, l: location, m: metadata}."""

    d: dict[str, Any]
    l: str
    m: Metadata

    @classmethod
    def create(cls, data: dict[str, Any], location: str) -> "ConfigWrapper":
        now = time.time()
        return cls(d=data, l=location, m=Metadata(created_at=now, updated_at=now, created_by=location))

    @classmethod
    def update(cls, data: dict[str, Any], location: str, meta: Metadata) -> "ConfigWrapper":
        return cls(d=data, l=location, m=Metadata(created_at=meta.created_at, updated_at=time.time(), created_by=meta.created_by))
