"""World Labs API client for 3D scene generation."""

import os
import time
from dataclasses import dataclass
from typing import Optional

import httpx

# World Labs API configuration
DEFAULT_API_BASE = "https://api.worldlabs.ai/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_POLL_INTERVAL = 2.0
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
        job_id: Unique identifier for the generation job.
        status: Final status of the job ('completed', 'failed', etc.).
        mesh_url: URL to download the generated mesh.
        mesh_data: Raw bytes of the mesh file (after download).
        file_type: Type of mesh file ('glb', 'gltf', etc.).
        metadata: Additional metadata from the API response.
    """

    job_id: str
    status: str
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
        >>> client = WorldLabsClient(api_key="wl_xxx")
        >>> result = client.generate("a wooden table")
        >>> print(result.mesh_data)  # GLB bytes
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
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "rebelai-python/0.1.0",
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
            error_msg = body.get("error", {}).get("message", response.text)
            raise WorldLabsAPIError(
                f"API error: {error_msg}",
                status_code=response.status_code,
                response_body=body,
            )

        return body

    def create_generation(
        self,
        prompt: str,
        style: Optional[str] = None,
        quality: str = "standard",
        output_format: str = "glb",
    ) -> str:
        """Create a new 3D generation job.

        Args:
            prompt: Text description of the scene to generate.
            style: Optional style preset (e.g., 'realistic', 'stylized').
            quality: Quality level ('draft', 'standard', 'high').
            output_format: Output mesh format ('glb', 'gltf', 'obj').

        Returns:
            Job ID for polling status.

        Raises:
            WorldLabsAPIError: If the API returns an error.
        """
        payload = {
            "prompt": prompt,
            "quality": quality,
            "output_format": output_format,
        }
        if style:
            payload["style"] = style

        response = self._client.post("/generations", json=payload)
        data = self._handle_response(response)

        job_id = data.get("id") or data.get("job_id")
        if not job_id:
            raise WorldLabsAPIError(
                "API response missing job ID",
                status_code=response.status_code,
                response_body=data,
            )

        return job_id

    def get_generation_status(self, job_id: str) -> dict:
        """Get the status of a generation job.

        Args:
            job_id: The job ID returned from create_generation.

        Returns:
            Dict with 'status', 'progress', and other job details.
        """
        response = self._client.get(f"/generations/{job_id}")
        return self._handle_response(response)

    def download_mesh(self, url: str) -> bytes:
        """Download mesh data from a URL.

        Args:
            url: URL to the mesh file.

        Returns:
            Raw bytes of the mesh file.
        """
        # Use a separate client for downloads (may be different host)
        with httpx.Client(timeout=60.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.content

    def generate(
        self,
        prompt: str,
        style: Optional[str] = None,
        quality: str = "standard",
        output_format: str = "glb",
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        max_wait: float = DEFAULT_MAX_WAIT,
    ) -> GenerationResult:
        """Generate a 3D scene and wait for completion.

        This is the high-level method that creates a job, polls for
        completion, and downloads the result.

        Args:
            prompt: Text description of the scene to generate.
            style: Optional style preset.
            quality: Quality level ('draft', 'standard', 'high').
            output_format: Output mesh format ('glb', 'gltf', 'obj').
            poll_interval: Seconds between status checks.
            max_wait: Maximum seconds to wait for completion.

        Returns:
            GenerationResult with mesh data.

        Raises:
            WorldLabsTimeoutError: If generation exceeds max_wait.
            WorldLabsAPIError: If generation fails.
        """
        # Create the generation job
        job_id = self.create_generation(
            prompt=prompt,
            style=style,
            quality=quality,
            output_format=output_format,
        )

        # Poll for completion
        start_time = time.time()
        while True:
            if time.time() - start_time > max_wait:
                raise WorldLabsTimeoutError(
                    f"Generation job {job_id} timed out after {max_wait} seconds"
                )

            status_data = self.get_generation_status(job_id)
            status = status_data.get("status", "unknown")

            if status == "completed":
                # Get the mesh URL
                mesh_url = (
                    status_data.get("output", {}).get("mesh_url")
                    or status_data.get("mesh_url")
                    or status_data.get("result", {}).get("url")
                )

                if not mesh_url:
                    raise WorldLabsAPIError(
                        "Completed job missing mesh URL",
                        status_code=200,
                        response_body=status_data,
                    )

                # Download the mesh
                mesh_data = self.download_mesh(mesh_url)

                return GenerationResult(
                    job_id=job_id,
                    status=status,
                    mesh_url=mesh_url,
                    mesh_data=mesh_data,
                    file_type=output_format,
                    metadata=status_data,
                )

            elif status in ("failed", "error", "cancelled"):
                error_msg = (
                    status_data.get("error", {}).get("message")
                    or status_data.get("error_message")
                    or f"Generation failed with status: {status}"
                )
                raise WorldLabsAPIError(
                    error_msg,
                    status_code=200,
                    response_body=status_data,
                )

            # Still in progress, wait and retry
            time.sleep(poll_interval)


def generate_mesh(
    prompt: str,
    api_key: Optional[str] = None,
    style: Optional[str] = None,
    quality: str = "standard",
    output_format: str = "glb",
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    max_wait: float = DEFAULT_MAX_WAIT,
) -> GenerationResult:
    """Generate a 3D scene from a text prompt using World Labs API.

    Convenience function that creates a client, generates the scene,
    and returns the result.

    Args:
        prompt: Text description of the scene to generate.
        api_key: World Labs API key. Reads from WORLD_LABS_API_KEY env var if not provided.
        style: Optional style preset.
        quality: Quality level ('draft', 'standard', 'high').
        output_format: Output mesh format ('glb', 'gltf', 'obj').
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
            style=style,
            quality=quality,
            output_format=output_format,
            poll_interval=poll_interval,
            max_wait=max_wait,
        )
