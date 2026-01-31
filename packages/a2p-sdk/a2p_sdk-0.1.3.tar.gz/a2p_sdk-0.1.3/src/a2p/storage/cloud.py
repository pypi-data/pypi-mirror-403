"""
Cloud storage backend for a2p profiles.

This storage backend connects to a2p-compatible REST APIs (like a2p-cloud)
via HTTP/REST to store and retrieve profiles.
"""

from typing import Any

import httpx

from a2p.client import ProfileStorage
from a2p.types import Profile


class CloudStorage(ProfileStorage):
    """
    Cloud storage backend that connects to a2p-compatible REST APIs.

    Supports services like a2p-cloud, custom implementations, etc.
    This enables using the a2p SDK with cloud-hosted profile services.

    Example:
        ```python
        storage = CloudStorage(
            api_url="https://api.a2p-cloud.example.com",
            auth_token="firebase-id-token",
            agent_did="did:a2p:agent:my-agent"
        )
        client = A2PClient(
            agent_did="did:a2p:agent:my-agent",
            storage=storage
        )
        ```
    """

    def __init__(
        self,
        api_url: str,
        auth_token: str,
        agent_did: str | None = None,
        timeout: float = 30.0,
        api_version: str = "v1",
    ):
        """
        Initialize cloud storage backend.

        Args:
            api_url: Base URL of the a2p-compatible API (e.g., "https://api.a2p-cloud.example.com")
            auth_token: Authentication token (Firebase ID token, API key, etc.)
            agent_did: Optional agent DID for identification
            timeout: HTTP request timeout in seconds
            api_version: API version to use (default: "v1")
        """
        self.api_url = api_url.rstrip("/")
        self.auth_token = auth_token
        self.agent_did = agent_did
        self.timeout = timeout
        self.api_version = api_version

        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "A2P-Version": "1.0",
        }

        if agent_did:
            headers["A2P-Agent-DID"] = agent_did

        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers=headers,
        )

    async def get(self, did: str, scopes: list[str] | None = None) -> Profile | None:
        """
        Get profile from cloud API.

        Args:
            did: Profile DID
            scopes: Optional list of scopes to request (e.g., ["a2p:identity", "a2p:preferences"])
                   If None, no scopes are requested and only minimal profile metadata is returned.

        Returns:
            Profile if found, None if not found

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        try:
            url = f"{self.api_url}/a2p/{self.api_version}/profile/{did}"
            if scopes:
                scopes_param = ",".join(scopes)
                url += f"?scopes={scopes_param}"

            response = await self._client.get(url)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()

            # Handle API response format: { success: true, data: {...}, meta: {...} }
            profile_data = data.get("data", data)
            return self._deserialize_profile(profile_data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
        except httpx.RequestError as e:
            raise ConnectionError(f"Failed to connect to a2p API: {e}") from e

    async def set(self, did: str, profile: Profile) -> None:
        """
        Update profile via cloud API.

        Note: This uses the user-facing API endpoint, not the protocol endpoint.
        For protocol-compatible updates, use the SDK's client methods.

        Args:
            did: Profile DID
            profile: Profile to store

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        payload = self._serialize_profile(profile)
        response = await self._client.put(f"{self.api_url}/api/profiles/{did}", json=payload)
        response.raise_for_status()

    async def delete(self, did: str) -> None:
        """
        Delete profile via cloud API.

        Args:
            did: Profile DID

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        response = await self._client.delete(f"{self.api_url}/api/profiles/{did}")
        response.raise_for_status()

    async def propose_memory(
        self,
        user_did: str,
        content: str,
        category: str | None = None,
        memory_type: str = "episodic",
        confidence: float = 0.7,
        context: str | None = None,
    ) -> dict[str, Any]:
        """
        Propose a new memory via the protocol endpoint.

        This uses the a2p protocol endpoint /a2p/v1/profile/:did/memories/propose
        which is the correct way for agents to propose memories to cloud-hosted profiles.

        Args:
            user_did: User profile DID
            content: Memory content
            category: Memory category (optional)
            memory_type: Memory type (episodic, semantic, procedural). Defaults to "episodic"
            confidence: Confidence score (0.0-1.0)
            context: Additional context (optional)

        Returns:
            Dictionary with proposal_id and status

        Raises:
            httpx.HTTPError: On HTTP errors
            ValueError: If memory_type is invalid
        """
        # Validate memory_type
        if memory_type not in ("episodic", "semantic", "procedural"):
            raise ValueError(
                f"Invalid memory_type: {memory_type}. "
                f"Must be one of: episodic, semantic, procedural"
            )

        payload = {
            "content": content,
            "memory_type": memory_type,
            "confidence": confidence,
        }

        if category:
            payload["category"] = category
        if context:
            payload["context"] = context

        response = await self._client.post(
            f"{self.api_url}/a2p/{self.api_version}/profile/{user_did}/memories/propose",
            json=payload,
        )
        response.raise_for_status()

        data = response.json()
        # Handle API response format: { success: true, data: {...}, meta: {...} }
        proposal_data = data.get("data", data)

        return {
            "proposal_id": proposal_data.get("proposalId") or proposal_data.get("proposal_id"),
            "status": proposal_data.get("status", "pending"),
        }

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        await self._client.aclose()

    def _serialize_profile(self, profile: Profile) -> dict:
        """
        Convert Profile Pydantic model to API JSON format.

        Handles version differences and ensures compatibility.
        """
        # Convert Profile to dict matching API schema
        return profile.model_dump(mode="json", exclude_none=True)

    def _deserialize_profile(self, data: dict) -> Profile:
        """
        Convert API response to Profile Pydantic model.

        Handles API response format and converts to SDK Profile type.
        """
        # Handle API response format - may have different field names
        # Map API fields to Profile model fields
        # Get profile DID (from id field or did field in response)
        profile_did = data.get("id") or data.get("did") or ""

        # Build profile dict, handling cases where scopes weren't requested
        profile_dict: dict[str, Any] = {
            "id": profile_did,
            "version": data.get("version", "0.1.0-alpha"),
            "profileType": data.get("profileType") or data.get("profile_type"),
        }

        # Only include sections that were returned (based on requested scopes)
        if "identity" in data:
            identity = data["identity"].copy() if isinstance(data["identity"], dict) else {}
            # Ensure identity.did is always set (required by Profile model)
            if "did" not in identity:
                identity["did"] = profile_did
            profile_dict["identity"] = identity
        else:
            # If identity not returned, create minimal identity with DID
            profile_dict["identity"] = {"did": profile_did}

        if "common" in data:
            profile_dict["common"] = data["common"]

        if "memories" in data:
            profile_dict["memories"] = data["memories"]

        if "settings" in data:
            profile_dict["settings"] = data["settings"]

        return Profile.model_validate(profile_dict)
