"""Collection class for managing entities."""

import asyncio
import logging
from collections.abc import Iterator
from typing import Any, Callable, Generic, Optional, Protocol, TypeVar, Union
from uuid import UUID

import msgspec

from .bucket import Bucket
from .fields import analyze_fields
from .struct import BrainlessStruct, ConfigWrapper, UniqueConstraintError, _register, _unregister

_log = logging.getLogger(__name__)


class HasUUID(Protocol):
    uuid: UUID


T = TypeVar("T", bound=HasUUID)


def _get_nested(obj: Any, path: str) -> Any:
    """Get nested attribute using __ separator."""
    for part in path.split("__"):
        if obj is None:
            return None
        obj = getattr(obj, part, None)
    return obj


class Collection(Generic[T]):
    """Collection of structs backed by NATS KV buckets."""

    def __init__(self, client: "BrainlessDB", cls: type[T]) -> None:
        if BrainlessStruct not in cls.__bases__:
            raise TypeError(f"{cls.__name__} must directly inherit from BrainlessStruct")

        self._client = client
        self._cls = cls
        self._analysis = analyze_fields(cls, client.namespace)

        self._entities: dict[str, T] = {}
        self._dirty: set[str] = set()
        self._deleted: set[str] = set()
        self._metadata: dict[str, Any] = {}
        # Auto-mark loaded if no NATS (pure in-memory mode)
        self._loaded = client._nats is None

        # Buckets (lazy)
        self._config_bucket: Optional[Bucket] = None
        self._state_bucket: Optional[Bucket] = None
        self._local_bucket: Optional[Bucket] = None

        # Watch
        self._watch_tasks: list[asyncio.Task] = []

        # Indexes: field -> value -> set of uids
        self._indexes: dict[str, dict[Any, set[str]]] = {
            f: {} for f in self._analysis.indexed_fields
        }
        # Uniques: field -> value -> uid
        self._uniques: dict[str, dict[Any, str]] = {
            f: {} for f in self._analysis.unique_fields
        }

        # Callbacks: list of (callback, trigger_local)
        self._on_change: list[tuple[Callable, bool]] = []
        self._on_delete: list[tuple[Callable, bool]] = []
        self._on_property: dict[str, list[tuple[Callable, bool]]] = {}

    @property
    def name(self) -> str:
        return self._cls.__name__.lower()

    # === Events ===

    def on_change(self, callback: Callable, trigger_local: bool = False) -> None:
        """Register callback(old_item, new_item) for changes."""
        self._on_change.append((callback, trigger_local))

    def on_delete(self, callback: Callable, trigger_local: bool = False) -> None:
        """Register callback(item) for deletions."""
        self._on_delete.append((callback, trigger_local))

    def on_property_change(self, trigger_local: bool = False, **kwargs: Callable) -> None:
        """Register callback(item, field, old, new) for property changes."""
        for field, cb in kwargs.items():
            self._on_property.setdefault(field, []).append((cb, trigger_local))

    def _fire_change(self, old: Optional[T], new: T, local: bool) -> None:
        for cb, trigger_local in self._on_change:
            if not local or trigger_local:
                cb(old, new)

        for field, cbs in self._on_property.items():
            old_val = _get_nested(old, field) if old else None
            new_val = _get_nested(new, field)
            if old_val != new_val:
                for cb, trigger_local in cbs:
                    if not local or trigger_local:
                        cb(new, field, old_val, new_val)

    def _fire_delete(self, item: T, local: bool) -> None:
        for cb, trigger_local in self._on_delete:
            if not local or trigger_local:
                cb(item)

    # === Indexing ===

    def _index_add(self, obj: T) -> None:
        uid = str(obj.uuid)
        for field in self._analysis.indexed_fields:
            val = getattr(obj, field, None)
            self._indexes[field].setdefault(val, set()).add(uid)
        for field in self._analysis.unique_fields:
            val = getattr(obj, field, None)
            if val is not None:
                self._uniques[field][val] = uid

    def _index_remove(self, obj: T) -> None:
        uid = str(obj.uuid)
        for field in self._analysis.indexed_fields:
            val = getattr(obj, field, None)
            if val in self._indexes[field]:
                self._indexes[field][val].discard(uid)
                if not self._indexes[field][val]:
                    del self._indexes[field][val]
        for field in self._analysis.unique_fields:
            val = getattr(obj, field, None)
            if val is not None and self._uniques[field].get(val) == uid:
                del self._uniques[field][val]

    def _check_unique(self, obj: T) -> None:
        """Check unique constraints, raise UniqueConstraintError if violated."""
        uid = str(obj.uuid)
        for field in self._analysis.unique_fields:
            val = getattr(obj, field, None)
            if val is None:
                continue
            existing = self._uniques[field].get(val)
            if existing and existing != uid:
                raise UniqueConstraintError(field, val)

    # === Data extraction ===

    def _to_config(self, obj: T) -> dict[str, Any]:
        data = {}
        for f in self._analysis.config_fields:
            val = getattr(obj, f, None)
            if val is not None:
                data[f] = msgspec.to_builtins(val) if hasattr(val, "__struct_fields__") else val
        return data

    def _to_state(self, obj: T) -> dict[str, Any]:
        return {f: getattr(obj, f, None) for f in self._analysis.state_fields}

    def _to_local(self, obj: Optional[T]) -> Optional[dict[str, Any]]:
        if obj is None or not self._analysis.local_class:
            return None
        local = getattr(obj, "_", None)
        return msgspec.to_builtins(local) if local else None

    def _from_parts(
        self,
        uid: str,
        config: dict,
        state: Optional[dict] = None,
        local: Optional[dict] = None,
    ) -> T:
        data: dict[str, Any] = {"_uuid": uid, **config}
        if state:
            data.update(state)
        if local and self._analysis.local_class:
            data["_"] = msgspec.convert(local, self._analysis.local_class)
        return msgspec.convert(data, self._cls)

    # === Buckets ===

    async def _ensure_buckets(self) -> bool:
        if not self._client.connected:
            return False

        a = self._analysis
        if not self._config_bucket:
            self._config_bucket = await self._client.get_bucket(a.config_bucket)
        if a.state_bucket and not self._state_bucket:
            self._state_bucket = await self._client.get_bucket(a.state_bucket)
        if a.local_bucket and not self._local_bucket:
            self._local_bucket = await self._client.get_bucket(a.local_bucket)
        return True

    @staticmethod
    async def _load_bucket(bucket: Optional[Bucket]) -> dict[str, dict]:
        if not bucket:
            return {}
        return {k: msgspec.json.decode(v) for k, v in (await bucket.all()).items()}

    # === CRUD ===

    def add(self, obj: Union[T, dict]) -> T:
        """Add or update struct in collection."""
        # Pre-process dict to inject local class type tag if needed
        if isinstance(obj, dict) and "_" in obj and isinstance(obj["_"], dict):
            local = obj["_"]
            if "type" not in local and self._analysis.local_class:
                obj = {**obj, "_": {**local, "type": self._analysis.local_class.__name__}}

        # Validate/convert - handles both struct and dict input
        obj = msgspec.convert(msgspec.to_builtins(obj), self._cls)

        uid = str(obj.uuid)
        old = self._entities.get(uid)

        self._check_unique(obj)

        if old:
            self._index_remove(old)

        self._entities[uid] = obj
        self._index_add(obj)
        self._dirty.add(uid)
        _register(obj.uuid, self)
        self._client.schedule_flush()
        self._fire_change(old, obj, local=True)
        return obj

    def get(self, uuid: str) -> Optional[T]:
        return self._entities.get(uuid)

    def delete(self, obj_or_uuid: Union[T, str]) -> bool:
        uid = obj_or_uuid if isinstance(obj_or_uuid, str) else str(obj_or_uuid.uuid)
        item = self._entities.get(uid)
        if not item:
            return False

        self._index_remove(item)
        _unregister(item.uuid)
        del self._entities[uid]
        self._dirty.discard(uid)
        self._deleted.add(uid)
        self._client.schedule_flush()
        self._fire_delete(item, local=True)
        return True

    def all(self) -> list[T]:
        return list(self._entities.values())

    def clear(self) -> None:
        for obj in self._entities.values():
            _unregister(obj.uuid)
        self._entities.clear()
        self._dirty.clear()
        self._metadata.clear()
        for idx in self._indexes.values():
            idx.clear()
        for uq in self._uniques.values():
            uq.clear()

    # === Filtering ===

    def _check_loaded(self) -> None:
        if not self._loaded:
            raise RuntimeError(f"Collection '{self.name}' not loaded. Call await collection.load() first.")

    def filter(
        self,
        predicate: Optional[Callable[[T], bool]] = None,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> list[T]:
        self._check_loaded()
        result: list[T] = []

        # Try indexed lookup first
        for field, value in kwargs.items():
            if "__" not in field and field in self._analysis.indexed_fields:
                uids = self._indexes[field].get(value, set())
                rest = {k: v for k, v in kwargs.items() if k != field}
                for uid in uids:
                    e = self._entities.get(uid)
                    if not e:
                        continue
                    if rest and not all(_get_nested(e, k) == v for k, v in rest.items()):
                        continue
                    if predicate and not predicate(e):
                        continue
                    result.append(e)
                    if limit and len(result) >= limit:
                        return result
                return result

        # Linear scan
        for e in self._entities.values():
            if predicate and not predicate(e):
                continue
            if kwargs and not all(_get_nested(e, k) == v for k, v in kwargs.items()):
                continue
            result.append(e)
            if limit and len(result) >= limit:
                break
        return result

    def find(self, predicate: Optional[Callable[[T], bool]] = None, **kwargs: Any) -> Optional[T]:
        result = self.filter(predicate, limit=1, **kwargs)
        return result[0] if result else None

    def order_by(self, field: str, reverse: bool = False) -> list[T]:
        self._check_loaded()
        return sorted(self._entities.values(), key=lambda e: _get_nested(e, field), reverse=reverse)

    # === Load / Flush ===

    async def load(self) -> int:
        if self._loaded:
            return 0
        if not await self._ensure_buckets():
            self._loaded = True
            return 0

        # Load from all buckets
        config_entries: dict[str, tuple[dict, Any]] = {}
        if self._config_bucket:
            for uid, raw in (await self._config_bucket.all()).items():
                w = msgspec.json.decode(raw, type=ConfigWrapper)
                config_entries[uid] = (w.d, w.m)
                self._metadata[uid] = w.m

        state = await self._load_bucket(self._state_bucket)
        local = await self._load_bucket(self._local_bucket)

        # Build entities
        for uid, (cfg, _) in config_entries.items():
            obj = self._from_parts(uid, cfg, state.get(uid), local.get(uid))
            self._entities[uid] = obj
            self._index_add(obj)
            _register(obj.uuid, self)

        self._loaded = True
        if config_entries:
            _log.info("Loaded %d entities into '%s'", len(config_entries), self.name)
        return len(config_entries)

    async def flush(self) -> int:
        connected = await self._ensure_buckets()
        ops = 0
        ns = self._client.namespace

        for uid in list(self._dirty):
            obj = self._entities.get(uid)
            if not obj:
                self._dirty.discard(uid)
                continue

            if connected:
                # Config
                cfg = self._to_config(obj)
                meta = self._metadata.get(uid)
                wrapper = ConfigWrapper.update(cfg, ns, meta) if meta else ConfigWrapper.create(cfg, ns)
                self._metadata[uid] = wrapper.m
                await self._config_bucket.put(uid, msgspec.json.encode(wrapper))

                # State
                if self._state_bucket and self._analysis.state_fields:
                    await self._state_bucket.put(uid, msgspec.json.encode(self._to_state(obj)))

                # Local
                local = self._to_local(obj)
                if self._local_bucket and local:
                    await self._local_bucket.put(uid, msgspec.json.encode(local))

            self._dirty.discard(uid)
            ops += 1

        for uid in list(self._deleted):
            if connected:
                await self._config_bucket.delete(uid)
                if self._state_bucket:
                    await self._state_bucket.delete(uid)
                if self._local_bucket:
                    await self._local_bucket.delete(uid)
            self._deleted.discard(uid)
            ops += 1

        return ops

    # === Watch ===

    async def watch(self) -> None:
        if not await self._ensure_buckets() or self._watch_tasks:
            return

        if self._config_bucket:
            self._watch_tasks.append(asyncio.create_task(self._watch_config()))
        if self._state_bucket:
            self._watch_tasks.append(asyncio.create_task(self._watch_bucket(self._state_bucket, "state")))
        if self._local_bucket:
            self._watch_tasks.append(asyncio.create_task(self._watch_bucket(self._local_bucket, "local")))

    async def unwatch(self) -> None:
        for task in self._watch_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._watch_tasks.clear()

    async def _watch_config(self) -> None:
        try:
            async for e in self._config_bucket.watch(include_history=False):
                uid = e.key
                # Skip if we have unflushed local changes
                if uid in self._dirty:
                    continue

                if e.operation == "DEL":
                    item = self._entities.get(uid)
                    if item:
                        self._index_remove(item)
                        _unregister(item.uuid)
                        del self._entities[uid]
                        self._metadata.pop(uid, None)
                        self._fire_delete(item, local=False)
                elif e.value:
                    w = msgspec.json.decode(e.value, type=ConfigWrapper)

                    old = self._entities.get(uid)
                    # Skip if data unchanged
                    if old and self._to_config(old) == w.d:
                        continue

                    self._metadata[uid] = w.m
                    if old:
                        self._index_remove(old)

                    new = self._from_parts(
                        uid, w.d,
                        self._to_state(old) if old else None,
                        self._to_local(old),
                    )
                    self._entities[uid] = new
                    self._index_add(new)
                    _register(new.uuid, self)
                    self._fire_change(old, new, local=False)
        except asyncio.CancelledError:
            pass
        except Exception as ex:
            _log.error("Config watch error in '%s': %s", self.name, ex)

    async def _watch_bucket(self, bucket: Bucket, kind: str) -> None:
        """Watch state or local bucket for changes."""
        try:
            async for e in bucket.watch(include_history=False):
                if e.key in self._dirty or e.operation == "DEL" or not e.value:
                    continue

                old = self._entities.get(e.key)
                if not old:
                    continue

                new_data = msgspec.json.decode(e.value)
                old_data = self._to_state(old) if kind == "state" else self._to_local(old)
                if old_data == new_data:
                    continue

                self._index_remove(old)
                if kind == "state":
                    new = self._from_parts(e.key, self._to_config(old), new_data, self._to_local(old))
                else:
                    new = self._from_parts(e.key, self._to_config(old), self._to_state(old), new_data)
                self._entities[e.key] = new
                self._index_add(new)
                _register(new.uuid, self)
                self._fire_change(old, new, local=False)
        except asyncio.CancelledError:
            pass
        except Exception as ex:
            _log.error("%s watch error in '%s': %s", kind.capitalize(), self.name, ex)

    # === Magic methods ===

    def __getitem__(self, uuid: str) -> T:
        if uuid not in self._entities:
            raise KeyError(uuid)
        return self._entities[uuid]

    def __delitem__(self, obj_or_uuid: Union[T, str]) -> None:
        uid = obj_or_uuid if isinstance(obj_or_uuid, str) else str(obj_or_uuid.uuid)
        if not self.delete(obj_or_uuid):
            raise KeyError(uid)

    def __contains__(self, obj_or_uuid: Union[T, str]) -> bool:
        uid = obj_or_uuid if isinstance(obj_or_uuid, str) else str(obj_or_uuid.uuid)
        return uid in self._entities

    def __iter__(self) -> Iterator[T]:
        return iter(self._entities.values())

    def __len__(self) -> int:
        return len(self._entities)

    def __repr__(self) -> str:
        return f"<Collection '{self.name}' ({len(self)} entities)>"
