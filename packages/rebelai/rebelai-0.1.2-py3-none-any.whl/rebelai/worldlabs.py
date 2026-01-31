"""World Labs API client for 3D scene generation."""

import os
import time
from dataclasses import dataclass
from typing import Optional

import httpx

# World Labs API configuration
DEFAULT_API_BASE = "https://api.worldlabs.ai/marble/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_POLL_INTERVAL = 5.0
DEFAULT_MAX_WAIT = 600.0  # 10 minutes max wait


class WorldLabsError(Exception):
    """Base exception for World Labs API errors."""

    pass


class WorldLabsAuthError(WorldLabsError):
    """Authentication error (invalid or missing API key)."""

    pass


class WorldLabsAPIError(WorldLabsError):
    """API returned an error response."""

    def __init__(self, message: str, status_code: int, response_body: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class WorldLabsTimeoutError(WorldLabsError):
    """Generation job timed out."""

    pass


@dataclass
class GenerationResult:
    """Result from a World Labs generation job.

    Attributes:
        operation_id: Unique identifier for the generation operation.
        world_id: ID of the generated world.
        status: Final status of the job ('SUCCEEDED', 'FAILED', etc.).
        mesh_url: URL to download the collider mesh (GLB format).
        mesh_data: Raw bytes of the mesh file (after download).
        file_type: Type of mesh file ('glb').
        metadata: Additional metadata from the API response.
    """

    operation_id: str
    world_id: Optional[str] = None
    status: str = ""
    mesh_url: Optional[str] = None
    mesh_data: Optional[bytes] = None
    file_type: str = "glb"
    metadata: Optional[dict] = None


class WorldLabsClient:
    """Client for the World Labs 3D generation API.

    Args:
        api_key: World Labs API key. If not provided, reads from
            WORLD_LABS_API_KEY environment variable.
        base_url: Base URL for the API. Defaults to production API.
        timeout: Request timeout in seconds.

    Raises:
        WorldLabsAuthError: If no API key is provided or found in environment.

    Example:
        >>> client = WorldLabsClient(api_key="your_api_key")
        >>> result = client.generate("a wooden table")
        >>> print(len(result.mesh_data))  # GLB bytes
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_API_BASE,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.api_key = api_key or os.environ.get("WORLD_LABS_API_KEY")
        if not self.api_key:
            raise WorldLabsAuthError(
                "No API key provided. Pass api_key parameter or set WORLD_LABS_API_KEY environment variable."
            )

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "WLT-Api-Key": self.api_key,
                "Content-Type": "application/json",
                "User-Agent": "rebelai-python/0.1.1",
            },
        )

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _handle_response(self, response: httpx.Response) -> dict:
        """Handle API response, raising appropriate errors."""
        if response.status_code == 401:
            raise WorldLabsAuthError("Invalid API key")
        if response.status_code == 403:
            raise WorldLabsAuthError("API key does not have permission for this operation")

        try:
            body = response.json()
        except Exception:
            body = {"raw": response.text}

        if response.status_code >= 400:
            error_msg = body.get("message", response.text)
            raise WorldLabsAPIError(
                f"API error: {error_msg}",
                status_code=response.status_code,
                response_body=body,
            )

        return body

    def create_generation(
        self,
        prompt: str,
        display_name: Optional[str] = None,
        model: str = "Marble 0.1-plus",
    ) -> str:
        """Create a new world generation job.

        Args:
            prompt: Text description of the scene to generate.
            display_name: Optional display name for the world.
            model: Model to use ('Marble 0.1-plus' or 'Marble 0.1-mini').

        Returns:
            Operation ID for polling status.

        Raises:
            WorldLabsAPIError: If the API returns an error.
        """
        payload = {
            "display_name": display_name or prompt[:50],
            "world_prompt": {
                "type": "text",
                "text_prompt": prompt,
            },
            "model": model,
        }

        response = self._client.post("/worlds:generate", json=payload)
        data = self._handle_response(response)

        operation_id = data.get("operation_id")
        if not operation_id:
            raise WorldLabsAPIError(
                "API response missing operation_id",
                status_code=response.status_code,
                response_body=data,
            )

        return operation_id

    def get_operation_status(self, operation_id: str) -> dict:
        """Get the status of a generation operation.

        Args:
            operation_id: The operation ID returned from create_generation.

        Returns:
            Dict with 'done', 'error', 'metadata', and 'response' fields.
        """
        response = self._client.get(f"/operations/{operation_id}")
        return self._handle_response(response)

    def download_mesh(self, url: str) -> bytes:
        """Download mesh data from a URL.

        Args:
            url: URL to the mesh file.

        Returns:
            Raw bytes of the mesh file.
        """
        with httpx.Client(timeout=120.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.content

    def generate(
        self,
        prompt: str,
        display_name: Optional[str] = None,
        model: str = "Marble 0.1-plus",
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        max_wait: float = DEFAULT_MAX_WAIT,
    ) -> GenerationResult:
        """Generate a 3D world and wait for completion.

        This is the high-level method that creates a job, polls for
        completion, and downloads the collider mesh.

        Args:
            prompt: Text description of the scene to generate.
            display_name: Optional display name for the world.
            model: Model to use ('Marble 0.1-plus' for quality, 'Marble 0.1-mini' for speed).
            poll_interval: Seconds between status checks.
            max_wait: Maximum seconds to wait for completion.

        Returns:
            GenerationResult with mesh data.

        Raises:
            WorldLabsTimeoutError: If generation exceeds max_wait.
            WorldLabsAPIError: If generation fails.
        """
        # Create the generation job
        operation_id = self.create_generation(
            prompt=prompt,
            display_name=display_name,
            model=model,
        )

        print(f"Started generation: {operation_id}")

        # Poll for completion
        start_time = time.time()
        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait:
                raise WorldLabsTimeoutError(
                    f"Generation timed out after {max_wait} seconds"
                )

            status_data = self.get_operation_status(operation_id)
            done = status_data.get("done", False)
            metadata = status_data.get("metadata", {})
            progress = metadata.get("progress", {})
            progress_status = progress.get("status", "UNKNOWN")
            progress_desc = progress.get("description", "")

            print(f"  [{int(elapsed)}s] {progress_status}: {progress_desc}")

            if done:
                error = status_data.get("error")
                if error:
                    raise WorldLabsAPIError(
                        f"Generation failed: {error}",
                        status_code=200,
                        response_body=status_data,
                    )

                response = status_data.get("response", {})
                world_id = response.get("id") or metadata.get("world_id")
                assets = response.get("assets", {})
                mesh_info = assets.get("mesh", {})
                mesh_url = mesh_info.get("collider_mesh_url")

                if not mesh_url:
                    raise WorldLabsAPIError(
                        "Completed job missing collider_mesh_url",
                        status_code=200,
                        response_body=status_data,
                    )

                # Download the mesh
                print(f"Downloading mesh...")
                mesh_data = self.download_mesh(mesh_url)
                print(f"Downloaded {len(mesh_data)} bytes")

                return GenerationResult(
                    operation_id=operation_id,
                    world_id=world_id,
                    status=progress_status,
                    mesh_url=mesh_url,
                    mesh_data=mesh_data,
                    file_type="glb",
                    metadata=status_data,
                )

            time.sleep(poll_interval)


def generate_mesh(
    prompt: str,
    api_key: Optional[str] = None,
    display_name: Optional[str] = None,
    model: str = "Marble 0.1-plus",
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    max_wait: float = DEFAULT_MAX_WAIT,
) -> GenerationResult:
    """Generate a 3D world from a text prompt using World Labs API.

    Convenience function that creates a client, generates the world,
    and returns the result.

    Args:
        prompt: Text description of the scene to generate.
        api_key: World Labs API key. Reads from WORLD_LABS_API_KEY env var if not provided.
        display_name: Optional display name for the world.
        model: Model to use ('Marble 0.1-plus' for quality, 'Marble 0.1-mini' for speed).
        poll_interval: Seconds between status checks.
        max_wait: Maximum seconds to wait for completion.

    Returns:
        GenerationResult with mesh data.

    Example:
        >>> result = generate_mesh("a red sports car")
        >>> with open("car.glb", "wb") as f:
        ...     f.write(result.mesh_data)
    """
    with WorldLabsClient(api_key=api_key) as client:
        return client.generate(
            prompt=prompt,
            display_name=display_name,
            model=model,
            poll_interval=poll_interval,
            max_wait=max_wait,
        )
