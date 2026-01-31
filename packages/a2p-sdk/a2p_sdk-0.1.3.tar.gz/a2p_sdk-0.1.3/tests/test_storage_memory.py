"""Tests for memory storage backend"""

import pytest

from a2p.core.profile import create_profile
from a2p.storage.memory import MemoryStorage


class TestMemoryStorage:
    """Test memory storage implementation"""

    @pytest.mark.asyncio
    async def test_get_set_profile(self):
        """Test getting and setting profiles"""
        storage = MemoryStorage()
        profile = create_profile()

        await storage.set(profile.id, profile)
        retrieved = await storage.get(profile.id)

        assert retrieved is not None
        assert retrieved.id == profile.id
        assert retrieved.version == profile.version

    @pytest.mark.asyncio
    async def test_get_nonexistent_profile(self):
        """Test getting non-existent profile returns None"""
        storage = MemoryStorage()

        result = await storage.get("did:a2p:user:test:nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_profile(self):
        """Test deleting profiles"""
        storage = MemoryStorage()
        profile = create_profile()

        await storage.set(profile.id, profile)
        await storage.delete(profile.id)

        result = await storage.get(profile.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_profile(self):
        """Test deleting non-existent profile does not raise error"""
        storage = MemoryStorage()

        # Should not raise an error
        await storage.delete("did:a2p:user:test:nonexistent")

    @pytest.mark.asyncio
    async def test_update_profile(self):
        """Test updating existing profile"""
        storage = MemoryStorage()
        profile = create_profile()
        profile.identity.display_name = "Original Name"

        await storage.set(profile.id, profile)

        # Update profile
        profile.identity.display_name = "Updated Name"
        await storage.set(profile.id, profile)

        retrieved = await storage.get(profile.id)
        assert retrieved is not None
        assert retrieved.identity.display_name == "Updated Name"

    @pytest.mark.asyncio
    async def test_multiple_profiles(self):
        """Test storing multiple profiles"""
        storage = MemoryStorage()
        profile1 = create_profile()
        profile2 = create_profile()

        await storage.set(profile1.id, profile1)
        await storage.set(profile2.id, profile2)

        retrieved1 = await storage.get(profile1.id)
        retrieved2 = await storage.get(profile2.id)

        assert retrieved1 is not None
        assert retrieved2 is not None
        assert retrieved1.id == profile1.id
        assert retrieved2.id == profile2.id
        assert retrieved1.id != retrieved2.id

    @pytest.mark.asyncio
    async def test_storage_isolation(self):
        """Test that storage instances are isolated"""
        storage1 = MemoryStorage()
        storage2 = MemoryStorage()
        profile = create_profile()

        await storage1.set(profile.id, profile)

        # Profile should not be in storage2
        result = await storage2.get(profile.id)
        assert result is None

        # Profile should be in storage1
        result = await storage1.get(profile.id)
        assert result is not None
