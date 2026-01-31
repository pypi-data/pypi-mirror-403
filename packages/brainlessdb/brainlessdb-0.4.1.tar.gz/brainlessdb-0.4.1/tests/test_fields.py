"""Tests for field analysis."""

from typing import Annotated, Optional, Union

from msgspec import Meta, Struct

from brainlessdb import BrainlessDBFeat, BrainlessStruct
from brainlessdb.fields import analyze_fields


class UcsV1(Struct):
    sid: int = 0
    pointer: int = 0


class AriV1(Struct):
    channel_id: str = ""


class SimpleV1(BrainlessStruct):
    """Simple struct with no state or app-local."""

    id: Annotated[int, Meta()] = 0
    name: Annotated[str, Meta()] = ""


class WithStateV1(BrainlessStruct):
    """Struct with state fields."""

    id: Annotated[int, Meta()] = 0
    name: Annotated[str, Meta()] = ""
    status: Annotated[
        int,
        Meta(extra={"brainlessdb_flags": BrainlessDBFeat.STATE}),
    ] = 0
    counter: Annotated[
        int,
        Meta(extra={"brainlessdb_flags": BrainlessDBFeat.STATE}),
    ] = 0


class WithLocalV1(BrainlessStruct):
    """Struct with app-local field."""

    id: Annotated[int, Meta()] = 0
    _: Optional[UcsV1] = None


class WithUnionLocalV1(BrainlessStruct):
    """Struct with Union app-local field."""

    id: Annotated[int, Meta()] = 0
    _: Union[UcsV1, AriV1, None] = None


class FullV1(BrainlessStruct):
    """Struct with config, state, and app-local."""

    id: Annotated[int, Meta()] = 0
    name: Annotated[str, Meta()] = ""
    status: Annotated[
        int,
        Meta(extra={"brainlessdb_flags": BrainlessDBFeat.STATE}),
    ] = 0
    _: Optional[UcsV1] = None


class TestAnalyzeFields:
    """Tests for analyze_fields function."""

    def test_simple_struct(self):
        """All fields go to config."""
        result = analyze_fields(SimpleV1, namespace="ucs")

        assert result.config_fields == {"id", "name"}
        assert result.state_fields == set()
        assert result.local_class is None

    def test_with_state_fields(self):
        """State fields separated from config."""
        result = analyze_fields(WithStateV1, namespace="ucs")

        assert result.config_fields == {"id", "name"}
        assert result.state_fields == {"status", "counter"}
        assert result.local_class is None

    def test_with_local_optional(self):
        """Optional app-local field detected."""
        result = analyze_fields(WithLocalV1, namespace="ucs")

        assert result.config_fields == {"id"}
        assert result.state_fields == set()
        assert result.local_class is UcsV1

    def test_with_local_union(self):
        """Union app-local field - correct class matched by namespace."""
        result = analyze_fields(WithUnionLocalV1, namespace="ucs")

        assert result.config_fields == {"id"}
        assert result.local_class is UcsV1

    def test_with_local_union_ari(self):
        """Union app-local field - ARI namespace."""
        result = analyze_fields(WithUnionLocalV1, namespace="ari")

        assert result.config_fields == {"id"}
        assert result.local_class is AriV1

    def test_with_local_no_match(self):
        """Union app-local field - no matching namespace."""
        result = analyze_fields(WithUnionLocalV1, namespace="other")

        assert result.config_fields == {"id"}
        assert result.local_class is None

    def test_full_struct(self):
        """Config, state, and app-local all separated."""
        result = analyze_fields(FullV1, namespace="ucs")

        assert result.config_fields == {"id", "name"}
        assert result.state_fields == {"status"}
        assert result.local_class is UcsV1

    def test_uuid_excluded(self):
        """UUID field excluded from config."""
        result = analyze_fields(SimpleV1, namespace="ucs")

        assert "UUID" not in result.config_fields
        assert "_uuid" not in result.config_fields

    def test_bucket_names(self):
        """Bucket names computed correctly."""
        result = analyze_fields(FullV1, namespace="ucs")

        assert result.config_bucket == "FullV1"
        assert result.state_bucket == "FullV1-State"
        assert result.local_bucket == "FullV1-UcsV1"

    def test_bucket_names_no_state(self):
        """State bucket is None when no state fields."""
        result = analyze_fields(SimpleV1, namespace="ucs")

        assert result.config_bucket == "SimpleV1"
        assert result.state_bucket is None
        assert result.local_bucket is None

    def test_bucket_names_no_local(self):
        """Local bucket is None when no match."""
        result = analyze_fields(WithUnionLocalV1, namespace="other")

        assert result.local_bucket is None
