"""
In-memory storage implementation for a2p profiles.

This is a simple storage backend that stores profiles in memory.
Useful for testing and local development.
"""

from a2p.client import ProfileStorage
from a2p.types import Profile


class MemoryStorage(ProfileStorage):
    """In-memory storage implementation"""

    def __init__(self) -> None:
        self._profiles: dict[str, Profile] = {}

    async def get(self, did: str) -> Profile | None:
        """Get a profile by DID"""
        return self._profiles.get(did)

    async def set(self, did: str, profile: Profile) -> None:
        """Store a profile"""
        self._profiles[did] = profile

    async def delete(self, did: str) -> None:
        """Delete a profile"""
        self._profiles.pop(did, None)
