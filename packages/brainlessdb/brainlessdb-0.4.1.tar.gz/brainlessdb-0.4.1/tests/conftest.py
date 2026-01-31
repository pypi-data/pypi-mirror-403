"""Test fixtures for brainless tests."""

from typing import Annotated, Optional

import pytest
from msgspec import Meta

from brainlessdb import BrainlessDB, BrainlessDBFeat, BrainlessStruct


class UserV1(BrainlessStruct):
    """Test user struct with indexed username."""

    id: Annotated[int, Meta()] = 0
    username: Annotated[
        str,
        Meta(extra={"brainlessdb_flags": BrainlessDBFeat.INDEX}),
    ] = ""
    email: Optional[Annotated[str, Meta()]] = None
    active: Annotated[bool, Meta()] = True


class ChannelV1(BrainlessStruct):
    """Test channel struct."""

    id: Annotated[str, Meta()] = ""
    name: Annotated[str, Meta()] = ""


class AgentV1(BrainlessStruct):
    """Test agent struct."""

    id: Annotated[int, Meta()] = 0
    channel: Optional[ChannelV1] = None


class QueueItemV1(BrainlessStruct):
    """Test queue item with nested structs."""

    inbound_id: Annotated[
        str,
        Meta(extra={"brainlessdb_flags": BrainlessDBFeat.INDEX}),
    ] = ""
    priority: Annotated[int, Meta()] = 0
    agents: Optional[AgentV1] = None


class UniqueUserV1(BrainlessStruct):
    """Test struct with UNIQUE field."""

    id: int = 0
    email: Annotated[
        Optional[str],
        Meta(extra={"brainlessdb_flags": BrainlessDBFeat.UNIQUE}),
    ] = None


@pytest.fixture
def db():
    """Create BrainlessDB instance without NATS."""
    return BrainlessDB(namespace="test")


@pytest.fixture
async def users(db):
    """Get users collection."""
    coll = db.collection(UserV1)
    await db.start()
    return coll


@pytest.fixture
async def queue(db):
    """Get queue collection."""
    coll = db.collection(QueueItemV1)
    await db.start()
    return coll


@pytest.fixture
async def unique_users(db):
    """Get unique users collection."""
    coll = db.collection(UniqueUserV1)
    await db.start()
    return coll
