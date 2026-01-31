"""Tests for Solid storage backend"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from a2p.storage.solid import SolidStorage


@pytest.fixture
def solid_storage():
    """Create SolidStorage instance for testing."""
    return SolidStorage(
        pod_url="https://alice.inrupt.com/profile/card#me",
        access_token="test-token",
    )


@pytest.fixture
def sample_profile():
    """Create a sample profile for testing."""
    from a2p.core.profile import create_profile

    profile = create_profile(
        did="did:a2p:user:local:alice",
        display_name="Alice",
    )
    return profile


@pytest.mark.asyncio
async def test_get_profile_exists(solid_storage, sample_profile):
    """Test getting an existing profile from Solid Pod."""
    profile_data = {
        "did:a2p:user:local:alice": sample_profile.model_dump(by_alias=True),
    }

    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=profile_data)
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance

        profile = await solid_storage.get(sample_profile.id)

        assert profile is not None
        assert profile.id == sample_profile.id


@pytest.mark.asyncio
async def test_get_profile_not_found(solid_storage):
    """Test getting a non-existent profile from Solid Pod."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        profile = await solid_storage.get("did:a2p:user:local:nonexistent")

        assert profile is None


@pytest.mark.asyncio
async def test_set_profile(solid_storage, sample_profile):
    """Test storing a profile in Solid Pod."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_instance.put = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance

        await solid_storage.set(sample_profile.id, sample_profile)

        # Verify PUT was called
        mock_client_instance.put.assert_called_once()
        call_args = mock_client_instance.put.call_args
        assert call_args[0][0] == solid_storage.profile_path


@pytest.mark.asyncio
async def test_delete_profile(solid_storage, sample_profile):
    """Test deleting a profile from Solid Pod."""
    # Create data with multiple profiles to test update path (not delete path)
    existing_data = {
        sample_profile.id: sample_profile.model_dump(by_alias=True, mode="json"),
        "did:a2p:user:local:other": {"id": "did:a2p:user:local:other"},
        "metadata": {"version": "0.1.0-alpha"},
    }

    with patch("httpx.AsyncClient") as mock_client:
        # Mock GET response (profile exists)
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json = MagicMock(return_value=existing_data)  # json() is sync
        mock_get_response.raise_for_status = MagicMock()

        # Mock PUT response (update after deletion)
        mock_put_response = MagicMock()
        mock_put_response.status_code = 200
        mock_put_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_instance.get = AsyncMock(return_value=mock_get_response)
        mock_client_instance.put = AsyncMock(return_value=mock_put_response)
        mock_client.return_value = mock_client_instance

        await solid_storage.delete(sample_profile.id)

        # Verify PUT was called to update
        mock_client_instance.put.assert_called_once()


@pytest.mark.asyncio
async def test_delete_profile_not_found(solid_storage):
    """Test deleting a non-existent profile."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance

        # Should not raise exception
        await solid_storage.delete("did:a2p:user:local:nonexistent")


def test_solid_storage_initialization():
    """Test SolidStorage initialization."""
    storage = SolidStorage(
        pod_url="https://alice.inrupt.com/profile/card#me",
        access_token="test-token",
    )

    assert storage.pod_url == "https://alice.inrupt.com/profile/card#me"
    assert storage.access_token == "test-token"
    assert storage.base_url == "https://alice.inrupt.com"
    assert storage.profile_path == "https://alice.inrupt.com/a2p/profile.json"


def test_solid_storage_base_url_extraction():
    """Test base URL extraction from different pod_url formats."""
    # Format 1: /profile/card#me
    storage1 = SolidStorage(
        pod_url="https://alice.inrupt.com/profile/card#me",
        access_token="token",
    )
    assert storage1.base_url == "https://alice.inrupt.com"
    assert storage1.profile_path == "https://alice.inrupt.com/a2p/profile.json"

    # Format 2: Just base URL
    storage2 = SolidStorage(
        pod_url="https://alice.inrupt.com",
        access_token="token",
    )
    assert storage2.base_url == "https://alice.inrupt.com"
    assert storage2.profile_path == "https://alice.inrupt.com/a2p/profile.json"
