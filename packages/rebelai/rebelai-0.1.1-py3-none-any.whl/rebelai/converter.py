"""Main conversion functions for RebelAI."""

from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from rebelai.mesh_processing import load_mesh, process_scene
from rebelai.mjcf_builder import build_mjcf
from rebelai.types import ConversionConfig

if TYPE_CHECKING:
    import mujoco


def load(
    source: Union[str, Path, bytes],
    config: ConversionConfig | None = None,
    file_type: str | None = None,
) -> "mujoco.MjModel":
    """Load a mesh file and convert to a MuJoCo model.

    This is the main entry point for RebelAI. It takes visual mesh data
    (e.g., from World Labs) and converts it to a physics-ready MuJoCo model
    with proper collision geometry.

    Args:
        source: Path to mesh file, or raw bytes of mesh data.
            Supported formats: GLTF, GLB, OBJ, STL, PLY.
        config: Conversion configuration. If None, uses defaults with
            convex decomposition for collision geometry.
        file_type: File format hint (e.g., 'glb', 'obj'). Required when
            source is bytes, optional for file paths.

    Returns:
        mujoco.MjModel ready for simulation.

    Raises:
        ValueError: If the mesh cannot be loaded or converted.

    Example:
        >>> import rebelai
        >>> import mujoco
        >>>
        >>> # Basic usage
        >>> model = rebelai.load("scene.glb")
        >>> data = mujoco.MjData(model)
        >>> mujoco.mj_step(model, data)
        >>>
        >>> # With custom config
        >>> from rebelai import ConversionConfig, CollisionMethod
        >>> config = ConversionConfig(
        ...     collision_method=CollisionMethod.CONVEX_DECOMPOSITION,
        ...     coacd_threshold=0.08,
        ...     density=500.0,
        ... )
        >>> model = rebelai.load("scene.glb", config=config)
    """
    if config is None:
        config = ConversionConfig()

    # Infer file type from path if not provided
    if file_type is None and isinstance(source, (str, Path)):
        file_type = Path(source).suffix.lstrip(".").lower()

    # Load mesh into trimesh scene
    scene = load_mesh(source, file_type=file_type)

    # Process meshes into collision geometry
    processed_meshes = process_scene(scene, config)

    if not processed_meshes:
        raise ValueError("No valid meshes found in input file")

    # Build MJCF XML
    mjcf_xml = build_mjcf(processed_meshes, config)

    # Create and return MuJoCo model
    try:
        import mujoco
    except ImportError as e:
        raise ImportError(
            "mujoco is required for load(). Install it with: pip install mujoco"
        ) from e

    try:
        model = mujoco.MjModel.from_xml_string(mjcf_xml)
    except Exception as e:
        raise ValueError(f"Failed to create MuJoCo model: {e}") from e

    return model


def load_from_file(
    path: Union[str, Path],
    config: ConversionConfig | None = None,
) -> "mujoco.MjModel":
    """Load a mesh file and convert to a MuJoCo model.

    Convenience function that explicitly takes a file path.
    See `load()` for full documentation.

    Args:
        path: Path to mesh file.
        config: Conversion configuration.

    Returns:
        mujoco.MjModel ready for simulation.
    """
    return load(path, config=config)


def to_mjcf(
    source: Union[str, Path, bytes],
    config: ConversionConfig | None = None,
    file_type: str | None = None,
) -> str:
    """Convert a mesh to MJCF XML without creating a MuJoCo model.

    Useful for debugging or saving the MJCF for later use.

    Args:
        source: Path to mesh file, or raw bytes of mesh data.
        config: Conversion configuration.
        file_type: File format hint.

    Returns:
        MJCF XML string.
    """
    if config is None:
        config = ConversionConfig()

    if file_type is None and isinstance(source, (str, Path)):
        file_type = Path(source).suffix.lstrip(".").lower()

    scene = load_mesh(source, file_type=file_type)
    processed_meshes = process_scene(scene, config)

    if not processed_meshes:
        raise ValueError("No valid meshes found in input file")

    return build_mjcf(processed_meshes, config)


def generate(
    prompt: str,
    api_key: Optional[str] = None,
    config: ConversionConfig | None = None,
    style: Optional[str] = None,
    quality: str = "standard",
    poll_interval: float = 2.0,
    max_wait: float = 600.0,
) -> "mujoco.MjModel":
    """Generate a 3D scene from text and convert to a MuJoCo model.

    This is the end-to-end function that calls World Labs API to generate
    a 3D scene from a text prompt, downloads the mesh, and converts it to
    a physics-ready MuJoCo model.

    Args:
        prompt: Text description of the scene to generate.
            Examples: "kitchen table with mugs", "red sports car", "office desk"
        api_key: World Labs API key. If not provided, reads from
            WORLD_LABS_API_KEY environment variable.
        config: Conversion configuration for physics geometry.
            If None, uses defaults with convex decomposition.
        style: Optional style preset for generation (e.g., 'realistic', 'stylized').
        quality: Generation quality ('draft', 'standard', 'high').
            Higher quality takes longer but produces better meshes.
        poll_interval: Seconds between status checks while waiting.
        max_wait: Maximum seconds to wait for generation to complete.

    Returns:
        mujoco.MjModel ready for simulation.

    Raises:
        WorldLabsAuthError: If API key is missing or invalid.
        WorldLabsAPIError: If generation fails.
        WorldLabsTimeoutError: If generation exceeds max_wait.
        ValueError: If mesh conversion fails.

    Example:
        >>> import rebelai
        >>> import mujoco
        >>>
        >>> # Basic usage (uses WORLD_LABS_API_KEY env var)
        >>> model = rebelai.generate("kitchen table with mugs")
        >>> data = mujoco.MjData(model)
        >>> mujoco.mj_step(model, data)
        >>>
        >>> # With explicit API key and config
        >>> from rebelai import ConversionConfig, CollisionMethod
        >>> config = ConversionConfig(
        ...     collision_method=CollisionMethod.CONVEX_DECOMPOSITION,
        ...     density=500.0,
        ... )
        >>> model = rebelai.generate(
        ...     "wooden chair",
        ...     api_key="wl_xxx",
        ...     config=config,
        ...     quality="high",
        ... )
    """
    from rebelai.worldlabs import generate_mesh

    # Generate the mesh via World Labs API
    result = generate_mesh(
        prompt=prompt,
        api_key=api_key,
        style=style,
        quality=quality,
        output_format="glb",
        poll_interval=poll_interval,
        max_wait=max_wait,
    )

    # Convert to MuJoCo model
    return load(
        source=result.mesh_data,
        config=config,
        file_type=result.file_type,
    )
