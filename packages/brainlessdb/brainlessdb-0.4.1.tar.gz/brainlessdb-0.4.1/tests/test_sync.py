"""Test multi-location sync."""

import asyncio

import pytest

from brainlessdb import BrainlessDB
from tests.conftest import UserV1
from tests.mock_nats import MockNats


class TestMultiLocationSync:
    """Test sync between multiple locations."""

    @pytest.mark.asyncio
    async def test_two_locations_see_same_data(self):
        """Both locations can read data written by either."""
        nats = MockNats()

        db1 = BrainlessDB(nats, namespace="loc1", flush_interval=0)
        db2 = BrainlessDB(nats, namespace="loc2", flush_interval=0)
        users1 = db1.collection(UserV1)
        users2 = db2.collection(UserV1)
        await db1.start()
        await db2.start()

        # Location 1 writes
        user = UserV1(id=1, username="alice")
        users1.add(user)
        await db1.flush()

        # Location 2 reloads and sees it
        users2.clear()
        users2._loaded = False
        await users2.load()
        loaded = users2.get(str(user.uuid))

        assert loaded is not None
        assert loaded.username == "alice"

        await db1.stop()
        await db2.stop()

    @pytest.mark.asyncio
    async def test_watch_receives_remote_changes(self):
        """Watch fires when other location makes changes."""
        nats = MockNats()

        db1 = BrainlessDB(nats, namespace="loc1", flush_interval=0)
        db2 = BrainlessDB(nats, namespace="loc2", flush_interval=0)
        users1 = db1.collection(UserV1)
        users2 = db2.collection(UserV1)
        await db1.start()
        await db2.start()

        # Location 2 watches
        changes = []
        users2.on_change(lambda old, new: changes.append((old, new)))
        await users2.watch()

        # Small delay for watch to start
        await asyncio.sleep(0.01)

        # Location 1 writes
        user = UserV1(id=1, username="alice")
        users1.add(user)
        await db1.flush()

        # Wait for watch to receive
        await asyncio.sleep(0.05)

        assert len(changes) == 1
        assert changes[0][0] is None  # old
        assert changes[0][1].username == "alice"  # new

        await db1.stop()
        await db2.stop()

    @pytest.mark.asyncio
    async def test_location_tracked_in_metadata(self):
        """Config bucket tracks which location made the change."""
        nats = MockNats()

        db1 = BrainlessDB(nats, namespace="loc1", flush_interval=0)
        users1 = db1.collection(UserV1)
        await db1.start()
        user = UserV1(id=1, username="alice")
        users1.add(user)
        await db1.flush()

        # Check metadata
        uuid = str(user.uuid)
        assert uuid in users1._metadata
        assert users1._metadata[uuid].created_by == "loc1"

        await db1.stop()

    @pytest.mark.asyncio
    async def test_remote_delete_fires_event(self):
        """Delete from one location fires event on other."""
        nats = MockNats()

        db1 = BrainlessDB(nats, namespace="loc1", flush_interval=0)
        db2 = BrainlessDB(nats, namespace="loc2", flush_interval=0)
        users1 = db1.collection(UserV1)
        users2 = db2.collection(UserV1)
        await db1.start()
        await db2.start()

        # Location 1 creates
        user = UserV1(id=1, username="alice")
        users1.add(user)
        await db1.flush()

        # Location 2 reloads and watches
        users2.clear()
        users2._loaded = False
        await users2.load()
        deleted = []
        users2.on_delete(lambda item: deleted.append(item))
        await users2.watch()
        await asyncio.sleep(0.01)

        # Location 1 deletes
        users1.delete(user)
        await db1.flush()
        await asyncio.sleep(0.05)

        assert len(deleted) == 1
        assert deleted[0].username == "alice"

        await db1.stop()
        await db2.stop()
