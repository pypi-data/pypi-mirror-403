"""
Solid Pod storage backend for a2p profiles.

This storage backend stores a2p profiles in Solid Pods (decentralized storage).
Users can store their profiles in their own Solid Pods, giving them full control.

Example:
    ```python
    from a2p.storage.solid import SolidStorage
    from a2p import A2PClient

    storage = SolidStorage(
        pod_url="https://alice.inrupt.com/profile/card#me",
        access_token="solid-access-token"
    )

    client = A2PClient(
        agent_did="did:a2p:agent:my-agent",
        storage=storage
    )
    ```
"""

import json

import httpx

from a2p.client import ProfileStorage
from a2p.types import Profile


class SolidStorage(ProfileStorage):
    """
    Solid Pod storage backend for a2p profiles.

    Stores profiles in user's Solid Pod using Solid Protocol.
    Requires authentication with the Pod provider.

    Attributes:
        pod_url: URL of the Solid Pod (e.g., "https://alice.inrupt.com/profile/card#me")
        access_token: Access token for authenticating with the Pod
        base_url: Base URL of the Pod (extracted from pod_url)
        timeout: HTTP request timeout in seconds
    """

    def __init__(
        self,
        pod_url: str,
        access_token: str,
        timeout: float = 30.0,
    ):
        """
        Initialize Solid storage backend.

        Args:
            pod_url: URL of the Solid Pod (WebID or profile card URL)
            access_token: Access token for Pod authentication
            timeout: HTTP request timeout in seconds
        """
        self.pod_url = pod_url
        self.access_token = access_token
        self.timeout = timeout

        # Extract base URL from pod_url
        # e.g., "https://alice.inrupt.com/profile/card#me" -> "https://alice.inrupt.com"
        from urllib.parse import urlparse

        parsed = urlparse(pod_url)
        # Remove fragment if present
        if parsed.fragment:
            base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        else:
            base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        # If path ends with /profile/card or similar, remove it
        if "/profile/card" in base:
            self.base_url = base.split("/profile/card")[0]
        elif base.count("/") > 2:
            # Remove trailing path segment
            self.base_url = base.rsplit("/", 1)[0]
        else:
            # Remove trailing slash if present
            self.base_url = base.rstrip("/")

        # Profile storage path in Pod
        self.profile_path = f"{self.base_url}/a2p/profile.json"

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for Solid requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def get(self, did: str) -> Profile | None:
        """
        Get a profile by DID from Solid Pod.

        Args:
            did: Profile DID

        Returns:
            Profile if found, None otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.profile_path,
                    headers=self._get_headers(),
                )

                if response.status_code == 404:
                    return None

                response.raise_for_status()
                data = response.json()

                # If profile is stored with DID key, extract it
                if isinstance(data, dict) and did in data:
                    profile_data = data[did]
                elif isinstance(data, dict) and "profile" in data:
                    profile_data = data["profile"]
                else:
                    profile_data = data

                return Profile.model_validate(profile_data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
        except Exception as e:
            raise Exception(f"Failed to get profile from Solid Pod: {e}") from e

    async def set(self, did: str, profile: Profile) -> None:
        """
        Store a profile in Solid Pod.

        Args:
            did: Profile DID
            profile: Profile to store
        """
        try:
            # Serialize profile to JSON (handles datetime serialization)
            profile_json = profile.model_dump(by_alias=True, exclude_none=True, mode="json")

            # Store with DID as key for easy lookup
            data = {
                did: profile_json,
                "metadata": {
                    "version": "0.1.0-alpha",
                    "updated": profile.updated.isoformat() if profile.updated else None,
                },
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # First, try to create directory if it doesn't exist
                # Solid Pods support creating resources via PUT
                response = await client.put(
                    self.profile_path,
                    headers=self._get_headers(),
                    content=json.dumps(data, indent=2, default=str),
                )

                response.raise_for_status()

        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                raise Exception(
                    "Permission denied: Cannot write to Solid Pod. "
                    "Check access token and Pod permissions."
                ) from e
            raise Exception(f"Failed to store profile in Solid Pod: {e}") from e
        except Exception as e:
            raise Exception(f"Failed to store profile in Solid Pod: {e}") from e

    async def delete(self, did: str) -> None:
        """
        Delete a profile from Solid Pod.

        Args:
            did: Profile DID to delete
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get current data
                response = await client.get(
                    self.profile_path,
                    headers=self._get_headers(),
                )

                if response.status_code == 404:
                    # Profile doesn't exist, nothing to delete
                    return

                response.raise_for_status()
                data = response.json()

                # Remove profile with this DID
                if isinstance(data, dict) and did in data:
                    del data[did]

                    # If no profiles left, delete the file
                    if not data or (len(data) == 1 and "metadata" in data):
                        response = await client.delete(
                            self.profile_path,
                            headers=self._get_headers(),
                        )
                    else:
                        # Update file with remaining profiles
                        response = await client.put(
                            self.profile_path,
                            headers=self._get_headers(),
                            content=json.dumps(data, indent=2),
                        )

                    response.raise_for_status()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Already deleted or doesn't exist
                return
            if e.response.status_code in (401, 403):
                raise Exception(
                    "Permission denied: Cannot delete from Solid Pod. "
                    "Check access token and Pod permissions."
                ) from e
            raise Exception(f"Failed to delete profile from Solid Pod: {e}") from e
        except Exception as e:
            raise Exception(f"Failed to delete profile from Solid Pod: {e}") from e
