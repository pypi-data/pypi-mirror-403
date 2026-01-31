"""Field analysis for multi-bucket storage."""

from dataclasses import dataclass
from typing import Annotated, Any, Optional, Union, get_args, get_origin, get_type_hints

import msgspec

from .struct import BrainlessDBFeat


@dataclass
class FieldAnalysis:
    """Result of analyzing struct fields."""

    cls: type
    namespace: str
    config_fields: set[str]
    state_fields: set[str]
    indexed_fields: set[str]
    unique_fields: set[str]
    local_class: Optional[type]

    @property
    def config_bucket(self) -> str:
        return self.cls.__name__

    @property
    def state_bucket(self) -> Optional[str]:
        return f"{self.cls.__name__}-State" if self.state_fields else None

    @property
    def local_bucket(self) -> Optional[str]:
        return f"{self.cls.__name__}-{self.local_class.__name__}" if self.local_class else None


def analyze_fields(cls: type, namespace: str) -> FieldAnalysis:
    """Analyze struct fields into config/state/indexed/local categories."""
    config: set[str] = set()
    state: set[str] = set()
    indexed: set[str] = set()
    unique: set[str] = set()
    local_cls: Optional[type] = None

    try:
        hints = get_type_hints(cls, include_extras=True)
    except (NameError, AttributeError):
        hints = {}

    for name, hint in hints.items():
        if name in ("UUID", "_uuid"):
            continue
        if name == "_":
            local_cls = _find_local_class(hint, namespace)
            continue

        flags = _get_flags(hint)
        if flags & BrainlessDBFeat.INDEX:
            indexed.add(name)
        if flags & BrainlessDBFeat.UNIQUE:
            unique.add(name)
            indexed.add(name)
        if flags & BrainlessDBFeat.STATE:
            state.add(name)
        else:
            config.add(name)

    return FieldAnalysis(cls, namespace, config, state, indexed, unique, local_cls)


def _get_flags(hint: Any) -> BrainlessDBFeat:
    """Extract brainlessdb flags from type hint."""
    if get_origin(hint) is None:
        return BrainlessDBFeat(0)

    for arg in get_args(hint):
        if isinstance(arg, msgspec.Meta):
            return (getattr(arg, "extra", None) or {}).get("brainlessdb_flags", BrainlessDBFeat(0))

    return BrainlessDBFeat(0)


def _find_local_class(hint: Any, namespace: str) -> Optional[type]:
    """Find class in Union matching namespace prefix."""
    candidates = _extract_classes(hint)
    ns = namespace.lower()
    for cls in candidates:
        if cls.__name__.lower().startswith(ns):
            return cls
    return None


def _extract_classes(hint: Any) -> list[type]:
    """Extract all non-None classes from a type hint."""
    # Unwrap Annotated
    if get_origin(hint) is Annotated:
        hint = get_args(hint)[0]

    # Handle Union/Optional
    if get_origin(hint) is Union:
        result = []
        for arg in get_args(hint):
            if arg is not type(None):
                result.extend(_extract_classes(arg))
        return result

    # Single class
    if hasattr(hint, "__name__"):
        return [hint]

    return []
