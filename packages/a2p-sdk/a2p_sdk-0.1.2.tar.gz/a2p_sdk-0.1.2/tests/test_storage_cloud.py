"""Tests for cloud storage backend"""

from unittest.mock import AsyncMock, patch

import pytest

from a2p.core.profile import create_profile
from a2p.storage.cloud import CloudStorage


class TestCloudStorage:
    """Test cloud storage implementation"""

    @pytest.mark.asyncio
    async def test_get_profile_success(self):
        """Test getting profile from cloud API"""
        storage = CloudStorage(api_url="https://api.example.com", auth_token="test-token")

        mock_profile = create_profile()
        mock_response = {"success": True, "data": {"profile": mock_profile.model_dump()}}

        with patch.object(storage._client, "get") as mock_get:
            mock_get.return_value = AsyncMock(
                status_code=200, json=lambda: mock_response, raise_for_status=lambda: None
            )

            result = await storage.get(mock_profile.id)

            assert result is not None
            assert result.id == mock_profile.id
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_profile_not_found(self):
        """Test getting non-existent profile returns None"""
        storage = CloudStorage(api_url="https://api.example.com", auth_token="test-token")

        with patch.object(storage._client, "get") as mock_get:
            mock_get.return_value = AsyncMock(status_code=404, raise_for_status=lambda: None)

            result = await storage.get("did:a2p:user:test:nonexistent")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_profile_with_scopes(self):
        """Test getting profile with scopes"""
        storage = CloudStorage(api_url="https://api.example.com", auth_token="test-token")

        mock_profile = create_profile()
        mock_response = {"success": True, "data": {"profile": mock_profile.model_dump()}}

        with patch.object(storage._client, "get") as mock_get:
            mock_get.return_value = AsyncMock(
                status_code=200, json=lambda: mock_response, raise_for_status=lambda: None
            )

            result = await storage.get(mock_profile.id, scopes=["a2p:identity", "a2p:preferences"])

            assert result is not None
            # Verify scopes were included in URL
            call_args = mock_get.call_args
            assert "scopes=" in str(call_args)

    @pytest.mark.asyncio
    async def test_set_profile(self):
        """Test setting profile via cloud API"""
        storage = CloudStorage(api_url="https://api.example.com", auth_token="test-token")

        profile = create_profile()
        mock_response = {"success": True, "data": {"profile": profile.model_dump()}}

        with patch.object(storage._client, "put") as mock_put:
            mock_put.return_value = AsyncMock(
                status_code=200, json=lambda: mock_response, raise_for_status=lambda: None
            )

            await storage.set(profile.id, profile)

            mock_put.assert_called_once()
            call_args = mock_put.call_args
            assert profile.id in str(call_args)

    @pytest.mark.asyncio
    async def test_delete_profile(self):
        """Test deleting profile via cloud API"""
        storage = CloudStorage(api_url="https://api.example.com", auth_token="test-token")

        profile_id = "did:a2p:user:test:123"

        with patch.object(storage._client, "delete") as mock_delete:
            mock_delete.return_value = AsyncMock(status_code=200, raise_for_status=lambda: None)

            await storage.delete(profile_id)

            mock_delete.assert_called_once()
            call_args = mock_delete.call_args
            assert profile_id in str(call_args)

    @pytest.mark.asyncio
    async def test_http_error_handling(self):
        """Test handling of HTTP errors"""
        storage = CloudStorage(api_url="https://api.example.com", auth_token="test-token")

        with patch.object(storage._client, "get") as mock_get:
            mock_get.return_value = AsyncMock(
                status_code=500, raise_for_status=AsyncMock(side_effect=Exception("Server error"))
            )

            with pytest.raises(Exception):
                await storage.get("did:a2p:user:test:123")

    @pytest.mark.asyncio
    async def test_propose_memory(self):
        """Test proposing memory via cloud API"""
        storage = CloudStorage(
            api_url="https://api.example.com",
            auth_token="test-token",
            agent_did="did:a2p:agent:test",
        )

        mock_response = {
            "success": True,
            "data": {"proposal": {"id": "prop_123", "status": "pending"}},
        }

        with patch.object(storage._client, "post") as mock_post:
            mock_post.return_value = AsyncMock(
                status_code=201, json=lambda: mock_response, raise_for_status=lambda: None
            )

            result = await storage.propose_memory(
                user_did="did:a2p:user:test:123",
                content="Test proposal",
                category="a2p:preferences",
            )

            assert result is not None
            assert result["id"] == "prop_123"
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_headers_included(self):
        """Test that authentication headers are included"""
        storage = CloudStorage(
            api_url="https://api.example.com",
            auth_token="test-token",
            agent_did="did:a2p:agent:test",
        )

        with patch.object(storage._client, "get") as mock_get:
            mock_get.return_value = AsyncMock(status_code=404, raise_for_status=lambda: None)

            await storage.get("did:a2p:user:test:123")

            # Verify headers were set in client initialization
            assert storage._client.headers["Authorization"] == "Bearer test-token"
            assert storage._client.headers["A2P-Agent-DID"] == "did:a2p:agent:test"
