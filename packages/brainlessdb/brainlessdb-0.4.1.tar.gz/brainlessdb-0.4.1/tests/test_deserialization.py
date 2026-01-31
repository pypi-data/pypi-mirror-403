"""Test deserialization of entities from bucket data.

These tests verify that field types are correctly preserved during
serialization/deserialization round-trips.
"""

from typing import Annotated, Optional, Union

import pytest
from msgspec import Meta, Struct, field

from brainlessdb import BrainlessDB, BrainlessDBFeat, BrainlessStruct
from brainlessdb.collection import Collection


class LocalData(Struct):
    """App-local data struct."""

    sid: int = 0
    count: int = 0


class EntityWithIntFields(BrainlessStruct):
    """Entity with various int fields in different buckets."""

    # Config field (no flags)
    config_int: int = 0

    # Indexed field
    indexed_int: Annotated[
        int,
        Meta(extra={"brainlessdb_flags": BrainlessDBFeat.INDEX}),
    ] = 0

    # State field
    state_int: Annotated[
        int,
        Meta(extra={"brainlessdb_flags": BrainlessDBFeat.STATE}),
    ] = 0

    # Unique field (auto-indexed)
    unique_int: Annotated[
        Optional[int],
        Meta(extra={"brainlessdb_flags": BrainlessDBFeat.UNIQUE}),
    ] = None

    # App-local field
    _: Optional[LocalData] = None


class EntityMixedTypes(BrainlessStruct):
    """Entity with mixed types to test type preservation."""

    int_field: int = 0
    str_field: str = ""
    bool_field: bool = False
    float_field: float = 0.0


@pytest.fixture
def db():
    return BrainlessDB(namespace="local")  # matches LocalData class name


@pytest.fixture
async def int_collection(db):
    coll = db.collection(EntityWithIntFields)
    await db.start()
    return coll


@pytest.fixture
async def mixed_collection(db):
    coll = db.collection(EntityMixedTypes)
    await db.start()
    return coll


class TestFieldAnalysis:
    """Test that field analysis correctly categorizes fields."""

    @pytest.mark.asyncio
    async def test_config_field_in_config(self, int_collection):
        assert "config_int" in int_collection._analysis.config_fields

    @pytest.mark.asyncio
    async def test_indexed_field_in_indexed(self, int_collection):
        assert "indexed_int" in int_collection._analysis.indexed_fields

    @pytest.mark.asyncio
    async def test_indexed_field_also_in_config(self, int_collection):
        # Indexed fields should still be stored in config bucket
        assert "indexed_int" in int_collection._analysis.config_fields

    @pytest.mark.asyncio
    async def test_state_field_in_state(self, int_collection):
        assert "state_int" in int_collection._analysis.state_fields

    @pytest.mark.asyncio
    async def test_state_field_not_in_config(self, int_collection):
        # State fields should NOT be in config
        assert "state_int" not in int_collection._analysis.config_fields

    @pytest.mark.asyncio
    async def test_unique_field_in_unique(self, int_collection):
        assert "unique_int" in int_collection._analysis.unique_fields

    @pytest.mark.asyncio
    async def test_unique_field_also_indexed(self, int_collection):
        # Unique implies indexed
        assert "unique_int" in int_collection._analysis.indexed_fields

    @pytest.mark.asyncio
    async def test_unique_field_also_in_config(self, int_collection):
        # Unique fields should be stored in config bucket
        assert "unique_int" in int_collection._analysis.config_fields


class TestFromPartsDeserialization:
    """Test _from_parts correctly deserializes data with proper types."""

    @pytest.mark.asyncio
    async def test_config_int_preserved(self, int_collection):
        """Int field in config should remain int after round-trip."""
        entity = EntityWithIntFields(config_int=42)
        int_collection.add(entity)

        # Simulate what happens during load: extract and reconstruct
        config = int_collection._to_config(entity)
        result = int_collection._from_parts(str(entity.uuid), config)

        assert result.config_int == 42
        assert isinstance(result.config_int, int), f"Expected int, got {type(result.config_int)}"

    @pytest.mark.asyncio
    async def test_indexed_int_preserved(self, int_collection):
        """Indexed int field should remain int after round-trip."""
        entity = EntityWithIntFields(indexed_int=123)
        int_collection.add(entity)

        config = int_collection._to_config(entity)
        result = int_collection._from_parts(str(entity.uuid), config)

        assert result.indexed_int == 123
        assert isinstance(result.indexed_int, int), f"Expected int, got {type(result.indexed_int)}"

    @pytest.mark.asyncio
    async def test_state_int_preserved(self, int_collection):
        """State int field should remain int after round-trip."""
        entity = EntityWithIntFields(state_int=456)
        int_collection.add(entity)

        config = int_collection._to_config(entity)
        state = int_collection._to_state(entity)
        result = int_collection._from_parts(str(entity.uuid), config, state)

        assert result.state_int == 456
        assert isinstance(result.state_int, int), f"Expected int, got {type(result.state_int)}"

    @pytest.mark.asyncio
    async def test_unique_int_preserved(self, int_collection):
        """Unique int field should remain int after round-trip."""
        entity = EntityWithIntFields(unique_int=789)
        int_collection.add(entity)

        config = int_collection._to_config(entity)
        result = int_collection._from_parts(str(entity.uuid), config)

        assert result.unique_int == 789
        assert isinstance(result.unique_int, int), f"Expected int, got {type(result.unique_int)}"

    @pytest.mark.asyncio
    async def test_local_int_preserved(self, int_collection):
        """Int field in app-local struct should remain int after round-trip."""
        entity = EntityWithIntFields(_=LocalData(sid=100, count=200))
        int_collection.add(entity)

        config = int_collection._to_config(entity)
        local = int_collection._to_local(entity)
        result = int_collection._from_parts(str(entity.uuid), config, None, local)

        assert result._.sid == 100
        assert isinstance(result._.sid, int), f"Expected int, got {type(result._.sid)}"
        assert result._.count == 200
        assert isinstance(result._.count, int), f"Expected int, got {type(result._.count)}"


class TestMixedTypesDeserialization:
    """Test that mixed types are all preserved correctly."""

    @pytest.mark.asyncio
    async def test_all_types_preserved(self, mixed_collection):
        """All field types should be preserved after round-trip."""
        entity = EntityMixedTypes(
            int_field=42,
            str_field="hello",
            bool_field=True,
            float_field=3.14,
        )
        mixed_collection.add(entity)

        config = mixed_collection._to_config(entity)
        result = mixed_collection._from_parts(str(entity.uuid), config)

        assert result.int_field == 42
        assert isinstance(result.int_field, int), f"int_field: Expected int, got {type(result.int_field)}"

        assert result.str_field == "hello"
        assert isinstance(result.str_field, str), f"str_field: Expected str, got {type(result.str_field)}"

        assert result.bool_field is True
        assert isinstance(result.bool_field, bool), f"bool_field: Expected bool, got {type(result.bool_field)}"

        assert result.float_field == 3.14
        assert isinstance(result.float_field, float), f"float_field: Expected float, got {type(result.float_field)}"


class TestToConfigExtraction:
    """Test _to_config extracts correct fields with correct types."""

    @pytest.mark.asyncio
    async def test_config_extracts_config_fields(self, int_collection):
        entity = EntityWithIntFields(config_int=42, indexed_int=123)
        config = int_collection._to_config(entity)

        assert "config_int" in config
        assert config["config_int"] == 42
        assert isinstance(config["config_int"], int)

    @pytest.mark.asyncio
    async def test_config_extracts_indexed_fields(self, int_collection):
        entity = EntityWithIntFields(indexed_int=123)
        config = int_collection._to_config(entity)

        assert "indexed_int" in config
        assert config["indexed_int"] == 123
        assert isinstance(config["indexed_int"], int)

    @pytest.mark.asyncio
    async def test_config_does_not_extract_state_fields(self, int_collection):
        entity = EntityWithIntFields(state_int=456)
        config = int_collection._to_config(entity)

        assert "state_int" not in config


class TestToStateExtraction:
    """Test _to_state extracts correct fields with correct types."""

    @pytest.mark.asyncio
    async def test_state_extracts_state_fields(self, int_collection):
        entity = EntityWithIntFields(state_int=456)
        state = int_collection._to_state(entity)

        assert "state_int" in state
        assert state["state_int"] == 456
        assert isinstance(state["state_int"], int)

    @pytest.mark.asyncio
    async def test_state_does_not_extract_config_fields(self, int_collection):
        entity = EntityWithIntFields(config_int=42)
        state = int_collection._to_state(entity)

        assert "config_int" not in state


class TestFullRoundTrip:
    """Test complete serialize/deserialize cycle."""

    @pytest.mark.asyncio
    async def test_full_entity_round_trip(self, int_collection):
        """Entity with all field types should survive full round-trip."""
        original = EntityWithIntFields(
            config_int=10,
            indexed_int=20,
            state_int=30,
            unique_int=40,
            _=LocalData(sid=50, count=60),
        )
        int_collection.add(original)

        # Extract all parts (simulating what flush does)
        config = int_collection._to_config(original)
        state = int_collection._to_state(original)
        local = int_collection._to_local(original)

        # Reconstruct (simulating what load does)
        restored = int_collection._from_parts(str(original.uuid), config, state, local)

        # Verify all values
        assert restored.config_int == 10
        assert restored.indexed_int == 20
        assert restored.state_int == 30
        assert restored.unique_int == 40
        assert restored._.sid == 50
        assert restored._.count == 60

        # Verify all types
        assert isinstance(restored.config_int, int)
        assert isinstance(restored.indexed_int, int)
        assert isinstance(restored.state_int, int)
        assert isinstance(restored.unique_int, int)
        assert isinstance(restored._.sid, int)
        assert isinstance(restored._.count, int)


class TestJsonRoundTrip:
    """Test serialize/deserialize with actual JSON encoding (like real bucket storage)."""

    @pytest.mark.asyncio
    async def test_config_through_json(self, int_collection):
        """Config dict should survive JSON encode/decode with correct types."""
        import msgspec

        original = EntityWithIntFields(config_int=42, indexed_int=123)
        config = int_collection._to_config(original)

        # Simulate bucket storage: encode to JSON bytes, decode back
        json_bytes = msgspec.json.encode(config)
        decoded_config = msgspec.json.decode(json_bytes)

        # Reconstruct from JSON-decoded data
        restored = int_collection._from_parts(str(original.uuid), decoded_config)

        assert restored.config_int == 42
        assert isinstance(restored.config_int, int), f"Expected int, got {type(restored.config_int)}"
        assert restored.indexed_int == 123
        assert isinstance(restored.indexed_int, int), f"Expected int, got {type(restored.indexed_int)}"

    @pytest.mark.asyncio
    async def test_state_through_json(self, int_collection):
        """State dict should survive JSON encode/decode with correct types."""
        import msgspec

        original = EntityWithIntFields(state_int=456)
        config = int_collection._to_config(original)
        state = int_collection._to_state(original)

        # Simulate bucket storage
        config_bytes = msgspec.json.encode(config)
        state_bytes = msgspec.json.encode(state)
        decoded_config = msgspec.json.decode(config_bytes)
        decoded_state = msgspec.json.decode(state_bytes)

        restored = int_collection._from_parts(str(original.uuid), decoded_config, decoded_state)

        assert restored.state_int == 456
        assert isinstance(restored.state_int, int), f"Expected int, got {type(restored.state_int)}"

    @pytest.mark.asyncio
    async def test_local_through_json(self, int_collection):
        """Local dict should survive JSON encode/decode with correct types."""
        import msgspec

        original = EntityWithIntFields(_=LocalData(sid=100, count=200))
        config = int_collection._to_config(original)
        local = int_collection._to_local(original)

        # Simulate bucket storage
        config_bytes = msgspec.json.encode(config)
        local_bytes = msgspec.json.encode(local)
        decoded_config = msgspec.json.decode(config_bytes)
        decoded_local = msgspec.json.decode(local_bytes)

        restored = int_collection._from_parts(str(original.uuid), decoded_config, None, decoded_local)

        assert restored._.sid == 100
        assert isinstance(restored._.sid, int), f"Expected int, got {type(restored._.sid)}"
        assert restored._.count == 200
        assert isinstance(restored._.count, int), f"Expected int, got {type(restored._.count)}"

    @pytest.mark.asyncio
    async def test_full_entity_through_json(self, int_collection):
        """Full entity should survive JSON round-trip like real bucket storage."""
        import msgspec
        from brainlessdb.struct import ConfigWrapper

        original = EntityWithIntFields(
            config_int=10,
            indexed_int=20,
            state_int=30,
            unique_int=40,
            _=LocalData(sid=50, count=60),
        )
        int_collection.add(original)

        # Extract parts
        config = int_collection._to_config(original)
        state = int_collection._to_state(original)
        local = int_collection._to_local(original)

        # Create wrapper like flush does
        wrapper = ConfigWrapper.create(config, "local")

        # Simulate bucket storage with JSON
        wrapper_bytes = msgspec.json.encode(wrapper)
        state_bytes = msgspec.json.encode(state)
        local_bytes = msgspec.json.encode(local)

        # Decode like load does
        decoded_wrapper = msgspec.json.decode(wrapper_bytes, type=ConfigWrapper)
        decoded_state = msgspec.json.decode(state_bytes)
        decoded_local = msgspec.json.decode(local_bytes)

        # Reconstruct
        restored = int_collection._from_parts(
            str(original.uuid),
            decoded_wrapper.d,
            decoded_state,
            decoded_local,
        )

        # Verify types
        assert isinstance(restored.config_int, int), f"config_int: got {type(restored.config_int)}"
        assert isinstance(restored.indexed_int, int), f"indexed_int: got {type(restored.indexed_int)}"
        assert isinstance(restored.state_int, int), f"state_int: got {type(restored.state_int)}"
        assert isinstance(restored.unique_int, int), f"unique_int: got {type(restored.unique_int)}"
        assert isinstance(restored._.sid, int), f"_.sid: got {type(restored._.sid)}"
        assert isinstance(restored._.count, int), f"_.count: got {type(restored._.count)}"


class TestRealWorldUserPattern:
    """Test patterns from real UserV1 struct that may have caused issues."""

    @pytest.mark.asyncio
    async def test_optional_annotated_int_pattern(self):
        """Test Optional[Annotated[int, Meta(...)]] pattern like queue_reason."""
        from enum import IntEnum
        import msgspec
        from brainlessdb import BrainlessDB, BrainlessDBFeat, BrainlessStruct
        from brainlessdb.struct import ConfigWrapper

        class Status(IntEnum):
            OFFLINE = 0
            ONLINE = 1

        class UserLike(BrainlessStruct):
            id: Annotated[int, Meta(extra={"brainlessdb_flags": BrainlessDBFeat.INDEX})] = 0
            group_id: int = 0
            # Pattern from queue_reason - Optional[Annotated[int, ...]]
            queue_reason: Optional[Annotated[int, Meta(description="")]] = None
            queue_status_changed: Optional[Annotated[int, Meta(description="")]] = None
            # State field with enum
            status: Annotated[Status, Meta(extra={"brainlessdb_flags": BrainlessDBFeat.STATE})] = Status.OFFLINE

        db = BrainlessDB(namespace="test")
        coll = db.collection(UserLike)
        await db.start()

        # Create entity with values
        original = UserLike(
            id=42,
            group_id=1,
            queue_reason=5,
            queue_status_changed=1234567890,
            status=Status.ONLINE,
        )
        coll.add(original)

        # Extract and serialize like flush does
        config = coll._to_config(original)
        state = coll._to_state(original)
        wrapper = ConfigWrapper.create(config, "test")

        # JSON round-trip like bucket storage
        wrapper_bytes = msgspec.json.encode(wrapper)
        state_bytes = msgspec.json.encode(state)

        decoded_wrapper = msgspec.json.decode(wrapper_bytes, type=ConfigWrapper)
        decoded_state = msgspec.json.decode(state_bytes)

        # Reconstruct like load does
        restored = coll._from_parts(str(original.uuid), decoded_wrapper.d, decoded_state)

        # Verify values
        assert restored.id == 42
        assert restored.group_id == 1
        assert restored.queue_reason == 5
        assert restored.queue_status_changed == 1234567890
        assert restored.status == Status.ONLINE

        # Verify types
        assert isinstance(restored.id, int), f"id: got {type(restored.id)}"
        assert isinstance(restored.group_id, int), f"group_id: got {type(restored.group_id)}"
        assert isinstance(restored.queue_reason, int), f"queue_reason: got {type(restored.queue_reason)}"
        assert isinstance(restored.queue_status_changed, int), f"queue_status_changed: got {type(restored.queue_status_changed)}"
        assert isinstance(restored.status, Status), f"status: got {type(restored.status)}"

    @pytest.mark.asyncio
    async def test_nested_struct_pattern(self):
        """Test nested struct like AgentChannelsV1."""
        import msgspec
        from brainlessdb import BrainlessDB, BrainlessStruct
        from brainlessdb.struct import ConfigWrapper

        class Channels(Struct):
            voice: int = 0
            chat: int = 0

        class UserWithChannels(BrainlessStruct):
            id: int = 0
            channels: Channels = field(default_factory=Channels)

        db = BrainlessDB(namespace="test")
        coll = db.collection(UserWithChannels)
        await db.start()

        original = UserWithChannels(id=1, channels=Channels(voice=2, chat=3))
        coll.add(original)

        config = coll._to_config(original)
        wrapper = ConfigWrapper.create(config, "test")

        # JSON round-trip
        wrapper_bytes = msgspec.json.encode(wrapper)
        decoded_wrapper = msgspec.json.decode(wrapper_bytes, type=ConfigWrapper)

        restored = coll._from_parts(str(original.uuid), decoded_wrapper.d)

        assert restored.id == 1
        assert restored.channels.voice == 2
        assert restored.channels.chat == 3
        assert isinstance(restored.channels, Channels)

    @pytest.mark.asyncio
    async def test_vcard_list_pattern(self):
        """Test list of nested structs like vcard: list[VCardV1]."""
        import msgspec
        from brainlessdb import BrainlessDB, BrainlessStruct
        from brainlessdb.struct import ConfigWrapper

        class VCard(Struct):
            name: str = ""
            value: str = ""

        class UserWithVCard(BrainlessStruct):
            id: int = 0
            vcard: Optional[list[VCard]] = None

        db = BrainlessDB(namespace="test")
        coll = db.collection(UserWithVCard)
        await db.start()

        original = UserWithVCard(
            id=1,
            vcard=[VCard(name="email", value="test@test.com"), VCard(name="phone", value="123")],
        )
        coll.add(original)

        config = coll._to_config(original)
        wrapper = ConfigWrapper.create(config, "test")

        # JSON round-trip
        wrapper_bytes = msgspec.json.encode(wrapper)
        decoded_wrapper = msgspec.json.decode(wrapper_bytes, type=ConfigWrapper)

        restored = coll._from_parts(str(original.uuid), decoded_wrapper.d)

        assert restored.id == 1
        assert len(restored.vcard) == 2
        assert restored.vcard[0].name == "email"
        assert restored.vcard[1].value == "123"


class TestLocalClassDetection:
    """Test _find_local_class handles various type patterns."""

    @pytest.mark.asyncio
    async def test_optional_annotated_union_pattern(self):
        """Test Optional[Annotated[Union[A, B], Meta()]] pattern from UserV2."""
        from brainlessdb import BrainlessDB, BrainlessStruct

        class AriLocal(Struct):
            counter: int = 0

        class UcsLocal(Struct):
            counter: int = 0

        class UserWithUnionLocal(BrainlessStruct):
            id: int = 0
            _: Optional[Annotated[Union[UcsLocal, AriLocal], Meta()]] = None

        # Test with "ari" namespace - should find AriLocal
        db_ari = BrainlessDB(namespace="ari")
        coll_ari = db_ari.collection(UserWithUnionLocal)
        assert coll_ari._analysis.local_class is AriLocal, f"Expected AriLocal, got {coll_ari._analysis.local_class}"

        # Test with "ucs" namespace - should find UcsLocal
        db_ucs = BrainlessDB(namespace="ucs")
        coll_ucs = db_ucs.collection(UserWithUnionLocal)
        assert coll_ucs._analysis.local_class is UcsLocal, f"Expected UcsLocal, got {coll_ucs._analysis.local_class}"

    @pytest.mark.asyncio
    async def test_optional_single_class_pattern(self):
        """Test Optional[LocalClass] pattern."""
        from brainlessdb import BrainlessDB, BrainlessStruct

        class TestLocal(Struct):
            value: int = 0

        class UserWithLocal(BrainlessStruct):
            id: int = 0
            _: Optional[TestLocal] = None

        db = BrainlessDB(namespace="test")
        coll = db.collection(UserWithLocal)
        assert coll._analysis.local_class is TestLocal

    @pytest.mark.asyncio
    async def test_union_without_optional_pattern(self):
        """Test Union[A, B] (without Optional) pattern."""
        from brainlessdb import BrainlessDB, BrainlessStruct

        class AriData(Struct):
            x: int = 0

        class UcsData(Struct):
            x: int = 0

        class UserUnion(BrainlessStruct):
            id: int = 0
            _: Union[UcsData, AriData] = field(default_factory=UcsData)

        db = BrainlessDB(namespace="ari")
        coll = db.collection(UserUnion)
        assert coll._analysis.local_class is AriData
