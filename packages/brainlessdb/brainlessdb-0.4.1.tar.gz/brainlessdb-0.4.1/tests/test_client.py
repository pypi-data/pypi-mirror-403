"""Test BrainlessDB client."""

import asyncio

import pytest

import brainlessdb
from brainlessdb import BrainlessDB

from .conftest import UserV1


class TestClient:
    """Test BrainlessDB client."""

    def test_create_client(self):
        db = BrainlessDB(namespace="test")
        assert db.namespace == "test"
        assert not db.connected

    def test_collection_by_type(self, db):
        users = db.collection(UserV1)
        assert users.name == "userv1"

    def test_same_collection_returned(self, db):
        c1 = db.collection(UserV1)
        c2 = db.collection(UserV1)
        assert c1 is c2


class TestFlushScheduling:
    """Test flush scheduling behavior."""

    @pytest.mark.asyncio
    async def test_flush_scheduled_on_add(self):
        db = BrainlessDB(namespace="test", flush_interval=0.05)
        users = db.collection(UserV1)
        await db.start()

        users.add(UserV1(id=1, username="alice"))
        assert db._flush_task is not None

        await asyncio.sleep(0.1)
        assert db._flush_task is None

    @pytest.mark.asyncio
    async def test_flush_immediate_when_interval_zero(self):
        db = BrainlessDB(namespace="test", flush_interval=0)
        users = db.collection(UserV1)
        await db.start()

        users.add(UserV1(id=1, username="alice"))
        await asyncio.sleep(0.01)
        assert len(users._dirty) == 0

    @pytest.mark.asyncio
    async def test_flush_debounced(self):
        db = BrainlessDB(namespace="test", flush_interval=0.1)
        users = db.collection(UserV1)
        await db.start()

        users.add(UserV1(id=1, username="alice"))
        task1 = db._flush_task

        users.add(UserV1(id=2, username="bob"))
        task2 = db._flush_task

        assert task1 is task2  # Same task, not rescheduled

        await asyncio.sleep(0.15)
        assert len(users._dirty) == 0


class TestGlobalAPI:
    """Test global singleton API."""

    @pytest.fixture(autouse=True)
    async def cleanup(self):
        yield
        await brainlessdb.stop()

    @pytest.mark.asyncio
    async def test_global_api_flow(self):
        brainlessdb.setup(namespace="test")
        users = brainlessdb.collection(UserV1)
        await brainlessdb.start()
        users.add(UserV1(id=1, username="alice"))
        assert await brainlessdb.flush() == 1
