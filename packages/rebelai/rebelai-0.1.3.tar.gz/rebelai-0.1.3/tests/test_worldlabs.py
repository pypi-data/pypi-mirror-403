"""Tests for World Labs API client."""

import os
from unittest.mock import MagicMock, patch

import pytest

from rebelai.worldlabs import (
    GenerationResult,
    WorldLabsAPIError,
    WorldLabsAuthError,
    WorldLabsClient,
    WorldLabsTimeoutError,
    generate_mesh,
)


class TestWorldLabsClient:
    """Tests for WorldLabsClient."""

    def test_init_with_api_key(self):
        """Test client initialization with explicit API key."""
        client = WorldLabsClient(api_key="wl_test_key")
        assert client.api_key == "wl_test_key"
        client.close()

    def test_init_with_env_var(self):
        """Test client initialization from environment variable."""
        with patch.dict(os.environ, {"WORLD_LABS_API_KEY": "wl_env_key"}):
            client = WorldLabsClient()
            assert client.api_key == "wl_env_key"
            client.close()

    def test_init_no_key_raises(self):
        """Test that missing API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove the env var if it exists
            os.environ.pop("WORLD_LABS_API_KEY", None)
            with pytest.raises(WorldLabsAuthError, match="No API key provided"):
                WorldLabsClient()

    def test_context_manager(self):
        """Test client works as context manager."""
        with WorldLabsClient(api_key="wl_test") as client:
            assert client.api_key == "wl_test"

    @patch("httpx.Client.post")
    def test_create_generation(self, mock_post):
        """Test creating a generation job."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "job_123"}
        mock_post.return_value = mock_response

        with WorldLabsClient(api_key="wl_test") as client:
            job_id = client.create_generation("a red car")

        assert job_id == "job_123"
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "/generations"
        assert call_args[1]["json"]["prompt"] == "a red car"

    @patch("httpx.Client.post")
    def test_create_generation_with_options(self, mock_post):
        """Test creating a generation job with all options."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "job_456"}
        mock_post.return_value = mock_response

        with WorldLabsClient(api_key="wl_test") as client:
            job_id = client.create_generation(
                prompt="wooden table",
                style="realistic",
                quality="high",
                output_format="obj",
            )

        assert job_id == "job_456"
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["prompt"] == "wooden table"
        assert payload["style"] == "realistic"
        assert payload["quality"] == "high"
        assert payload["output_format"] == "obj"

    @patch("httpx.Client.post")
    def test_create_generation_auth_error(self, mock_post):
        """Test authentication error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": {"message": "Invalid API key"}}
        mock_post.return_value = mock_response

        with WorldLabsClient(api_key="wl_bad_key") as client:
            with pytest.raises(WorldLabsAuthError, match="Invalid API key"):
                client.create_generation("test")

    @patch("httpx.Client.post")
    def test_create_generation_api_error(self, mock_post):
        """Test API error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": {"message": "Invalid prompt"}}
        mock_response.text = "Invalid prompt"
        mock_post.return_value = mock_response

        with WorldLabsClient(api_key="wl_test") as client:
            with pytest.raises(WorldLabsAPIError, match="Invalid prompt"):
                client.create_generation("")

    @patch("httpx.Client.get")
    def test_get_generation_status(self, mock_get):
        """Test getting generation status."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "job_123",
            "status": "processing",
            "progress": 50,
        }
        mock_get.return_value = mock_response

        with WorldLabsClient(api_key="wl_test") as client:
            status = client.get_generation_status("job_123")

        assert status["status"] == "processing"
        assert status["progress"] == 50
        mock_get.assert_called_once_with("/generations/job_123")

    @patch("httpx.Client.get")
    def test_download_mesh(self, mock_get):
        """Test downloading mesh data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"GLB_BINARY_DATA"
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
            mock_client_instance.__exit__ = MagicMock(return_value=False)
            mock_client_class.return_value = mock_client_instance

            with WorldLabsClient(api_key="wl_test") as client:
                data = client.download_mesh("https://cdn.worldlabs.ai/mesh.glb")

        assert data == b"GLB_BINARY_DATA"


class TestGenerateFunction:
    """Tests for the generate_mesh function."""

    @patch("rebelai.worldlabs.WorldLabsClient")
    def test_generate_mesh_success(self, mock_client_class):
        """Test successful mesh generation."""
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        mock_client.generate.return_value = GenerationResult(
            job_id="job_123",
            status="completed",
            mesh_url="https://cdn.worldlabs.ai/mesh.glb",
            mesh_data=b"GLB_DATA",
            file_type="glb",
        )

        result = generate_mesh("a wooden chair", api_key="wl_test")

        assert result.job_id == "job_123"
        assert result.status == "completed"
        assert result.mesh_data == b"GLB_DATA"
        mock_client.generate.assert_called_once()

    @patch("rebelai.worldlabs.WorldLabsClient")
    def test_generate_mesh_passes_options(self, mock_client_class):
        """Test that options are passed through."""
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.generate.return_value = GenerationResult(
            job_id="job_123", status="completed", mesh_data=b"DATA"
        )

        generate_mesh(
            "table",
            api_key="wl_test",
            style="realistic",
            quality="high",
            poll_interval=5.0,
            max_wait=120.0,
        )

        mock_client.generate.assert_called_once_with(
            prompt="table",
            style="realistic",
            quality="high",
            output_format="glb",
            poll_interval=5.0,
            max_wait=120.0,
        )


class TestClientGenerate:
    """Tests for the client.generate() method."""

    @patch.object(WorldLabsClient, "create_generation")
    @patch.object(WorldLabsClient, "get_generation_status")
    @patch.object(WorldLabsClient, "download_mesh")
    def test_generate_polls_until_complete(
        self, mock_download, mock_status, mock_create
    ):
        """Test that generate polls until job completes."""
        mock_create.return_value = "job_123"
        mock_status.side_effect = [
            {"status": "processing", "progress": 25},
            {"status": "processing", "progress": 75},
            {
                "status": "completed",
                "output": {"mesh_url": "https://cdn.worldlabs.ai/mesh.glb"},
            },
        ]
        mock_download.return_value = b"MESH_DATA"

        with WorldLabsClient(api_key="wl_test") as client:
            result = client.generate("test prompt", poll_interval=0.01)

        assert result.status == "completed"
        assert result.mesh_data == b"MESH_DATA"
        assert mock_status.call_count == 3

    @patch.object(WorldLabsClient, "create_generation")
    @patch.object(WorldLabsClient, "get_generation_status")
    def test_generate_handles_failure(self, mock_status, mock_create):
        """Test that generate raises on job failure."""
        mock_create.return_value = "job_123"
        mock_status.return_value = {
            "status": "failed",
            "error": {"message": "Content policy violation"},
        }

        with WorldLabsClient(api_key="wl_test") as client:
            with pytest.raises(WorldLabsAPIError, match="Content policy violation"):
                client.generate("test", poll_interval=0.01)

    @patch.object(WorldLabsClient, "create_generation")
    @patch.object(WorldLabsClient, "get_generation_status")
    def test_generate_timeout(self, mock_status, mock_create):
        """Test that generate raises on timeout."""
        mock_create.return_value = "job_123"
        mock_status.return_value = {"status": "processing", "progress": 50}

        with WorldLabsClient(api_key="wl_test") as client:
            with pytest.raises(WorldLabsTimeoutError, match="timed out"):
                client.generate("test", poll_interval=0.01, max_wait=0.05)


class TestGenerationResult:
    """Tests for GenerationResult dataclass."""

    def test_default_values(self):
        """Test default values."""
        result = GenerationResult(job_id="123", status="completed")
        assert result.job_id == "123"
        assert result.status == "completed"
        assert result.mesh_url is None
        assert result.mesh_data is None
        assert result.file_type == "glb"
        assert result.metadata is None

    def test_all_values(self):
        """Test with all values set."""
        result = GenerationResult(
            job_id="456",
            status="completed",
            mesh_url="https://example.com/mesh.glb",
            mesh_data=b"data",
            file_type="obj",
            metadata={"key": "value"},
        )
        assert result.job_id == "456"
        assert result.mesh_url == "https://example.com/mesh.glb"
        assert result.mesh_data == b"data"
        assert result.file_type == "obj"
        assert result.metadata == {"key": "value"}
