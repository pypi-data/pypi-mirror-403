"""Test Collection CRUD and filtering."""

import pytest

from brainlessdb import BrainlessDB, UniqueConstraintError

from tests.conftest import AgentV1, ChannelV1, QueueItemV1, UniqueUserV1, UserV1


class TestCollectionCRUD:
    """Test basic CRUD operations."""

    @pytest.mark.asyncio
    async def test_add_and_get(self, users):
        user = UserV1(id=1, username="alice")
        users.add(user)

        result = users.get(str(user.uuid))
        assert result.uuid == user.uuid
        assert result.username == "alice"

    @pytest.mark.asyncio
    async def test_add_multiple(self, users):
        u1 = UserV1(id=1, username="alice")
        u2 = UserV1(id=2, username="bob")
        users.add(u1)
        users.add(u2)

        assert len(users) == 2
        assert users.get(str(u1.uuid)).username == "alice"
        assert users.get(str(u2.uuid)).username == "bob"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, users):
        assert users.get("nonexistent") is None

    @pytest.mark.asyncio
    async def test_delete_by_object(self, users):
        user = UserV1(id=1, username="alice")
        users.add(user)

        assert users.delete(user) is True
        assert len(users) == 0

    @pytest.mark.asyncio
    async def test_delete_by_uuid(self, users):
        user = UserV1(id=1, username="alice")
        users.add(user)

        assert users.delete(str(user.uuid)) is True
        assert len(users) == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, users):
        assert users.delete("nonexistent") is False

    @pytest.mark.asyncio
    async def test_contains(self, users):
        user = UserV1(id=1, username="alice")
        assert user not in users
        assert str(user.uuid) not in users

        users.add(user)
        assert user in users
        assert str(user.uuid) in users

    @pytest.mark.asyncio
    async def test_getitem(self, users):
        user = UserV1(id=1, username="alice")
        users.add(user)
        assert users[str(user.uuid)].uuid == user.uuid

    @pytest.mark.asyncio
    async def test_getitem_raises(self, users):
        with pytest.raises(KeyError):
            _ = users["nonexistent"]

    @pytest.mark.asyncio
    async def test_delitem(self, users):
        user = UserV1(id=1, username="alice")
        users.add(user)
        del users[user]
        assert len(users) == 0

    @pytest.mark.asyncio
    async def test_delitem_raises(self, users):
        with pytest.raises(KeyError):
            del users["nonexistent"]

    @pytest.mark.asyncio
    async def test_iter(self, users):
        u1 = UserV1(id=1, username="alice")
        u2 = UserV1(id=2, username="bob")
        users.add(u1)
        users.add(u2)

        items = list(users)
        assert len(items) == 2
        assert u1 in items
        assert u2 in items

    @pytest.mark.asyncio
    async def test_all(self, users):
        u1 = UserV1(id=1, username="alice")
        u2 = UserV1(id=2, username="bob")
        users.add(u1)
        users.add(u2)
        assert len(users.all()) == 2

    @pytest.mark.asyncio
    async def test_clear(self, users):
        users.add(UserV1(id=1, username="alice"))
        users.add(UserV1(id=2, username="bob"))
        users.clear()
        assert len(users) == 0


class TestCollectionFilter:
    """Test filtering and find operations."""

    @pytest.mark.asyncio
    async def test_not_loaded_raises(self, db):
        # Simulate NATS mode (not auto-loaded) - create collection directly
        from brainlessdb.collection import Collection
        db._nats = object()  # fake NATS
        coll = Collection(db, UserV1)  # bypass async collection()
        with pytest.raises(RuntimeError, match="not loaded"):
            coll.filter()

    @pytest.mark.asyncio
    async def test_filter_predicate(self, users):
        users.add(UserV1(id=1, username="alice", active=True))
        users.add(UserV1(id=2, username="bob", active=False))
        users.add(UserV1(id=3, username="carol", active=True))

        result = users.filter(lambda u: u.active)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_filter_kwargs(self, users):
        users.add(UserV1(id=1, username="alice", active=True))
        users.add(UserV1(id=2, username="bob", active=False))
        users.add(UserV1(id=3, username="carol", active=True))

        result = users.filter(active=True)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_filter_no_match(self, users):
        users.add(UserV1(id=1, username="alice", active=True))
        result = users.filter(lambda u: not u.active)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_find_predicate(self, users):
        users.add(UserV1(id=1, username="alice"))
        users.add(UserV1(id=2, username="bob"))

        result = users.find(lambda u: u.id == 2)
        assert result is not None
        assert result.username == "bob"

    @pytest.mark.asyncio
    async def test_find_kwargs(self, users):
        users.add(UserV1(id=1, username="alice"))
        users.add(UserV1(id=2, username="bob"))

        result = users.find(id=2)
        assert result is not None
        assert result.username == "bob"

    @pytest.mark.asyncio
    async def test_find_no_match(self, users):
        users.add(UserV1(id=1, username="alice"))
        assert users.find(lambda u: u.id == 999) is None

    @pytest.mark.asyncio
    async def test_filter_with_limit(self, users):
        users.add(UserV1(id=1, username="alice", active=True))
        users.add(UserV1(id=2, username="bob", active=True))
        users.add(UserV1(id=3, username="carol", active=True))

        result = users.filter(active=True, limit=2)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_filter_predicate_and_kwargs(self, users):
        users.add(UserV1(id=1, username="alice", active=True))
        users.add(UserV1(id=2, username="alice", active=False))
        users.add(UserV1(id=3, username="bob", active=True))

        # Combine indexed kwarg with predicate
        result = users.filter(lambda u: u.id > 1, username="alice")
        assert len(result) == 1
        assert result[0].id == 2

    @pytest.mark.asyncio
    async def test_order_by(self, users):
        users.add(UserV1(id=3, username="carol"))
        users.add(UserV1(id=1, username="alice"))
        users.add(UserV1(id=2, username="bob"))

        result = users.order_by("id")
        assert [u.id for u in result] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_order_by_reverse(self, users):
        users.add(UserV1(id=3, username="carol"))
        users.add(UserV1(id=1, username="alice"))
        users.add(UserV1(id=2, username="bob"))

        result = users.order_by("id", reverse=True)
        assert [u.id for u in result] == [3, 2, 1]


class TestNestedFilter:
    """Test nested attribute filtering with __ syntax."""

    @pytest.mark.asyncio
    async def test_find_nested_kwargs(self, queue):
        channel = ChannelV1(id="ch-123", name="test")
        agent = AgentV1(id=1, channel=channel)
        item = QueueItemV1(inbound_id="call-1", agents=agent)
        queue.add(item)

        result = queue.find(agents__channel__id="ch-123")
        assert result.uuid == item.uuid

    @pytest.mark.asyncio
    async def test_filter_nested_kwargs(self, queue):
        channel = ChannelV1(id="ch-123", name="test")
        agent = AgentV1(id=1, channel=channel)
        queue.add(QueueItemV1(inbound_id="call-1", agents=agent))
        queue.add(QueueItemV1(inbound_id="call-2"))

        result = queue.filter(agents__channel__id="ch-123")
        assert len(result) == 1
        assert result[0].inbound_id == "call-1"

    @pytest.mark.asyncio
    async def test_filter_simple_field(self, queue):
        queue.add(QueueItemV1(inbound_id="call-1"))
        queue.add(QueueItemV1(inbound_id="call-2"))
        queue.add(QueueItemV1(inbound_id="call-1"))

        result = queue.filter(inbound_id="call-1")
        assert len(result) == 2


class TestIndex:
    """Test field indexing with INDEX flag."""

    @pytest.mark.asyncio
    async def test_indexed_fields_detected(self, users):
        assert "username" in users._analysis.indexed_fields

    @pytest.mark.asyncio
    async def test_index_updated_on_add(self, users):
        user = UserV1(id=1, username="alice")
        users.add(user)

        assert "alice" in users._indexes["username"]
        assert str(user.uuid) in users._indexes["username"]["alice"]

    @pytest.mark.asyncio
    async def test_index_updated_on_delete(self, users):
        user = UserV1(id=1, username="alice")
        users.add(user)
        users.delete(user)

        assert "alice" not in users._indexes["username"]

    @pytest.mark.asyncio
    async def test_index_updated_on_update(self, users):
        user = UserV1(id=1, username="alice")
        users.add(user)

        user2 = UserV1(_uuid=user.uuid, id=1, username="alice_updated")
        users.add(user2)

        assert "alice" not in users._indexes["username"]
        assert "alice_updated" in users._indexes["username"]

    @pytest.mark.asyncio
    async def test_filter_uses_index(self, users):
        users.add(UserV1(id=1, username="alice"))
        users.add(UserV1(id=2, username="bob"))
        users.add(UserV1(id=3, username="alice"))

        # Filter by indexed field should use index
        result = users.filter(username="alice")
        assert len(result) == 2
        assert all(u.username == "alice" for u in result)

    @pytest.mark.asyncio
    async def test_find_uses_index(self, users):
        users.add(UserV1(id=1, username="alice"))
        users.add(UserV1(id=2, username="bob"))

        # Find by indexed field should use index
        result = users.find(username="bob")
        assert result is not None
        assert result.id == 2

    @pytest.mark.asyncio
    async def test_filter_indexed_with_additional_kwargs(self, users):
        users.add(UserV1(id=1, username="alice", active=True))
        users.add(UserV1(id=2, username="alice", active=False))
        users.add(UserV1(id=3, username="bob", active=True))

        # Filter by indexed + non-indexed field
        result = users.filter(username="alice", active=True)
        assert len(result) == 1
        assert result[0].id == 1

    @pytest.mark.asyncio
    async def test_clear_clears_indexes(self, users):
        users.add(UserV1(id=1, username="alice"))
        users.add(UserV1(id=2, username="bob"))
        users.clear()

        assert len(users._indexes["username"]) == 0


class TestEvents:
    """Test event callbacks."""

    @pytest.mark.asyncio
    async def test_on_change_new_item(self, users):
        changes = []
        users.on_change(lambda old, new: changes.append((old, new)), trigger_local=True)

        user = UserV1(id=1, username="alice")
        users.add(user)

        assert len(changes) == 1
        assert changes[0][0] is None  # old_item
        assert changes[0][1].uuid == user.uuid  # new_item

    @pytest.mark.asyncio
    async def test_on_change_update_item(self, users):
        changes = []
        users.on_change(lambda old, new: changes.append((old, new)), trigger_local=True)

        user = UserV1(id=1, username="alice")
        users.add(user)

        user2 = UserV1(_uuid=user.uuid, id=1, username="alice_updated")
        users.add(user2)

        assert len(changes) == 2
        assert changes[1][0].uuid == user.uuid  # old_item
        assert changes[1][1].uuid == user2.uuid  # new_item

    @pytest.mark.asyncio
    async def test_on_change_no_trigger_local(self, users):
        changes = []
        users.on_change(lambda old, new: changes.append((old, new)), trigger_local=False)

        users.add(UserV1(id=1, username="alice"))
        assert len(changes) == 0  # Not triggered for local changes

    @pytest.mark.asyncio
    async def test_on_delete(self, users):
        deleted = []
        users.on_delete(lambda item: deleted.append(item), trigger_local=True)

        user = UserV1(id=1, username="alice")
        users.add(user)
        users.delete(user)

        assert len(deleted) == 1
        assert deleted[0].uuid == user.uuid

    @pytest.mark.asyncio
    async def test_on_delete_no_trigger_local(self, users):
        deleted = []
        users.on_delete(lambda item: deleted.append(item), trigger_local=False)

        user = UserV1(id=1, username="alice")
        users.add(user)
        users.delete(user)

        assert len(deleted) == 0

    @pytest.mark.asyncio
    async def test_on_property_change(self, users):
        changes = []
        users.on_property_change(
            trigger_local=True,
            username=lambda item, field, old, new: changes.append((field, old, new)),
        )

        user = UserV1(id=1, username="alice")
        users.add(user)

        user2 = UserV1(_uuid=user.uuid, id=1, username="bob")
        users.add(user2)

        assert len(changes) == 2
        assert changes[0] == ("username", None, "alice")  # new item
        assert changes[1] == ("username", "alice", "bob")  # update

    @pytest.mark.asyncio
    async def test_on_property_change_nested(self, queue):
        changes = []
        queue.on_property_change(
            trigger_local=True,
            agents__channel__id=lambda item, field, old, new: changes.append((old, new)),
        )

        channel = ChannelV1(id="ch-1", name="test")
        agent = AgentV1(id=1, channel=channel)
        item = QueueItemV1(inbound_id="call-1", agents=agent)
        queue.add(item)

        assert len(changes) == 1
        assert changes[0] == (None, "ch-1")


class TestStruct:
    """Test struct behavior."""

    def test_uuid_unique(self):
        u1 = UserV1(id=1, username="alice")
        u2 = UserV1(id=2, username="bob")
        assert u1.uuid != u2.uuid


class TestUnique:
    """Test UNIQUE field constraint."""

    @pytest.mark.asyncio
    async def test_unique_fields_detected(self, unique_users):
        assert "email" in unique_users._analysis.unique_fields

    @pytest.mark.asyncio
    async def test_unique_implies_indexed(self, unique_users):
        # UNIQUE fields should automatically be indexed
        assert "email" in unique_users._analysis.indexed_fields

    @pytest.mark.asyncio
    async def test_unique_find_uses_index(self, unique_users):
        unique_users.add(UniqueUserV1(id=1, email="alice@test.com"))
        unique_users.add(UniqueUserV1(id=2, email="bob@test.com"))
        # find by unique field uses index
        result = unique_users.find(email="bob@test.com")
        assert result is not None
        assert result.id == 2

    @pytest.mark.asyncio
    async def test_unique_add_different_values(self, unique_users):
        unique_users.add(UniqueUserV1(id=1, email="alice@test.com"))
        unique_users.add(UniqueUserV1(id=2, email="bob@test.com"))
        assert len(unique_users) == 2

    @pytest.mark.asyncio
    async def test_unique_add_duplicate_raises(self, unique_users):
        unique_users.add(UniqueUserV1(id=1, email="alice@test.com"))
        with pytest.raises(UniqueConstraintError) as exc:
            unique_users.add(UniqueUserV1(id=2, email="alice@test.com"))
        assert exc.value.field == "email"
        assert exc.value.value == "alice@test.com"

    @pytest.mark.asyncio
    async def test_unique_update_same_entity(self, unique_users):
        user = UniqueUserV1(id=1, email="alice@test.com")
        unique_users.add(user)
        # Update same entity - should work
        user2 = UniqueUserV1(_uuid=user.uuid, id=1, email="alice@test.com")
        unique_users.add(user2)
        assert len(unique_users) == 1

    @pytest.mark.asyncio
    async def test_unique_update_to_new_value(self, unique_users):
        user = UniqueUserV1(id=1, email="alice@test.com")
        unique_users.add(user)
        # Update to new value - should work
        user2 = UniqueUserV1(_uuid=user.uuid, id=1, email="alice_new@test.com")
        unique_users.add(user2)
        assert len(unique_users) == 1
        # Old value should be freed
        unique_users.add(UniqueUserV1(id=2, email="alice@test.com"))
        assert len(unique_users) == 2

    @pytest.mark.asyncio
    async def test_unique_delete_frees_value(self, unique_users):
        user = UniqueUserV1(id=1, email="alice@test.com")
        unique_users.add(user)
        unique_users.delete(user)
        # Now should be able to add same email
        unique_users.add(UniqueUserV1(id=2, email="alice@test.com"))
        assert len(unique_users) == 1

    @pytest.mark.asyncio
    async def test_unique_clear_frees_all(self, unique_users):
        unique_users.add(UniqueUserV1(id=1, email="alice@test.com"))
        unique_users.add(UniqueUserV1(id=2, email="bob@test.com"))
        unique_users.clear()
        # Now should be able to add same emails
        unique_users.add(UniqueUserV1(id=3, email="alice@test.com"))
        unique_users.add(UniqueUserV1(id=4, email="bob@test.com"))
        assert len(unique_users) == 2

    @pytest.mark.asyncio
    async def test_unique_none_value_allowed_multiple(self, unique_users):
        # None values should not be constrained (like SQL NULL)
        unique_users.add(UniqueUserV1(id=1, email=None))
        unique_users.add(UniqueUserV1(id=2, email=None))
        assert len(unique_users) == 2

    @pytest.mark.asyncio
    async def test_unique_empty_string_is_constrained(self, unique_users):
        # Empty string is a value, should be unique
        unique_users.add(UniqueUserV1(id=1, email=""))
        with pytest.raises(UniqueConstraintError):
            unique_users.add(UniqueUserV1(id=2, email=""))
