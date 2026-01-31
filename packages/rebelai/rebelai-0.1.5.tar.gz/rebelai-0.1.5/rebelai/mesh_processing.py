"""Mesh loading and convex decomposition."""

from pathlib import Path
from typing import Union

import coacd
import numpy as np
import trimesh

from rebelai.types import CollisionGeom, CollisionMethod, ConversionConfig, ProcessedMesh


def load_mesh(source: Union[str, Path, bytes], file_type: str | None = None) -> trimesh.Scene:
    """Load a mesh file into a trimesh Scene.

    Args:
        source: File path or raw bytes of the mesh data.
        file_type: File format hint (e.g., 'glb', 'gltf', 'obj', 'stl').
            Required when source is bytes.

    Returns:
        A trimesh Scene containing all meshes.

    Raises:
        ValueError: If file cannot be loaded or format is unsupported.
    """
    try:
        if isinstance(source, bytes):
            if file_type is None:
                raise ValueError("file_type required when loading from bytes")
            loaded = trimesh.load(
                trimesh.util.wrap_as_stream(source),
                file_type=file_type,
                force="scene",
            )
        else:
            path = Path(source)
            if not path.exists():
                raise ValueError(f"File not found: {path}")
            loaded = trimesh.load(str(path), force="scene")

        # Ensure we have a Scene
        if isinstance(loaded, trimesh.Trimesh):
            scene = trimesh.Scene()
            scene.add_geometry(loaded, node_name="mesh_0")
            return scene
        elif isinstance(loaded, trimesh.Scene):
            return loaded
        else:
            raise ValueError(f"Unexpected mesh type: {type(loaded)}")

    except Exception as e:
        raise ValueError(f"Failed to load mesh: {e}") from e


def _compute_convex_hull(mesh: trimesh.Trimesh) -> CollisionGeom:
    """Compute a single convex hull for a mesh."""
    hull = mesh.convex_hull
    return CollisionGeom(
        name="hull",
        vertices=np.array(hull.vertices, dtype=np.float64),
        faces=np.array(hull.faces, dtype=np.int32),
        geom_type="mesh",
    )


def _compute_bounding_box(mesh: trimesh.Trimesh) -> CollisionGeom:
    """Compute an axis-aligned bounding box."""
    bounds = mesh.bounds
    center = (bounds[0] + bounds[1]) / 2
    half_extents = (bounds[1] - bounds[0]) / 2

    return CollisionGeom(
        name="bbox",
        vertices=np.array([]),
        faces=np.array([]),
        position=tuple(center),
        geom_type="box",
        size=tuple(half_extents),
    )


def _compute_bounding_primitives(mesh: trimesh.Trimesh) -> CollisionGeom:
    """Fit the best bounding primitive to the mesh."""
    # Try to find minimum bounding box
    try:
        obb = mesh.bounding_box_oriented
        # Use oriented bounding box
        transform = obb.primitive.transform
        extents = obb.primitive.extents

        # Extract position and rotation from transform
        position = transform[:3, 3]

        # Convert rotation matrix to quaternion
        from trimesh.transformations import quaternion_from_matrix

        quat = quaternion_from_matrix(transform)

        return CollisionGeom(
            name="primitive",
            vertices=np.array([]),
            faces=np.array([]),
            position=tuple(position),
            quaternion=(quat[0], quat[1], quat[2], quat[3]),
            geom_type="box",
            size=tuple(extents / 2),
        )
    except Exception:
        # Fallback to AABB
        return _compute_bounding_box(mesh)


def _compute_convex_decomposition(
    mesh: trimesh.Trimesh, config: ConversionConfig
) -> list[CollisionGeom]:
    """Decompose mesh into convex parts using CoACD."""
    # Prepare mesh for CoACD
    vertices = np.array(mesh.vertices, dtype=np.float64)
    faces = np.array(mesh.faces, dtype=np.int32)

    # Run CoACD decomposition
    try:
        parts = coacd.run_coacd(
            coacd.Mesh(vertices, faces),
            threshold=config.coacd_threshold,
            max_convex_hull=config.coacd_max_convex_hull,
        )
    except Exception as e:
        # Fallback to convex hull if decomposition fails
        print(f"CoACD decomposition failed, falling back to convex hull: {e}")
        return [_compute_convex_hull(mesh)]

    geoms = []
    for i, part in enumerate(parts):
        # CoACD returns list of [vertices, faces] pairs
        part_verts = np.array(part[0], dtype=np.float64)
        part_faces = np.array(part[1], dtype=np.int32)

        # Create convex hull of each part to ensure convexity
        part_mesh = trimesh.Trimesh(vertices=part_verts, faces=part_faces)
        hull = part_mesh.convex_hull

        geoms.append(
            CollisionGeom(
                name=f"hull_{i}",
                vertices=np.array(hull.vertices, dtype=np.float64),
                faces=np.array(hull.faces, dtype=np.int32),
                geom_type="mesh",
            )
        )

    return geoms if geoms else [_compute_convex_hull(mesh)]


def process_mesh(
    mesh: trimesh.Trimesh,
    name: str,
    config: ConversionConfig,
    transform: np.ndarray | None = None,
) -> ProcessedMesh:
    """Process a single mesh into collision geometry.

    Args:
        mesh: Input trimesh.
        name: Name for the processed mesh.
        config: Conversion configuration.
        transform: Optional 4x4 transform matrix to apply.

    Returns:
        ProcessedMesh with visual and collision data.
    """
    # Apply transform if provided
    if transform is not None:
        mesh = mesh.copy()
        mesh.apply_transform(transform)

    # Optional simplification
    if config.simplify and len(mesh.faces) > config.target_faces:
        mesh = mesh.simplify_quadric_decimation(config.target_faces)

    # Merge close vertices
    if config.merge_threshold > 0:
        mesh.merge_vertices()

    # Generate collision geometry based on method
    if config.collision_method == CollisionMethod.CONVEX_HULL:
        collision_geoms = [_compute_convex_hull(mesh)]
    elif config.collision_method == CollisionMethod.CONVEX_DECOMPOSITION:
        collision_geoms = _compute_convex_decomposition(mesh, config)
    elif config.collision_method == CollisionMethod.BOUNDING_BOX:
        collision_geoms = [_compute_bounding_box(mesh)]
    elif config.collision_method == CollisionMethod.PRIMITIVES:
        collision_geoms = [_compute_bounding_primitives(mesh)]
    elif config.collision_method == CollisionMethod.PASSTHROUGH:
        collision_geoms = [
            CollisionGeom(
                name="passthrough",
                vertices=np.array(mesh.vertices, dtype=np.float64),
                faces=np.array(mesh.faces, dtype=np.int32),
                geom_type="mesh",
            )
        ]
    else:
        raise ValueError(f"Unknown collision method: {config.collision_method}")

    # Compute mass from volume
    try:
        volume = abs(mesh.volume)
        mass = volume * config.density
        if mass < 1e-6:
            mass = 0.1  # Minimum mass
    except Exception:
        mass = 1.0  # Default mass

    return ProcessedMesh(
        name=name,
        visual_vertices=np.array(mesh.vertices, dtype=np.float64),
        visual_faces=np.array(mesh.faces, dtype=np.int32),
        collision_geoms=collision_geoms,
        mass=mass,
    )


def process_scene(scene: trimesh.Scene, config: ConversionConfig) -> list[ProcessedMesh]:
    """Process all meshes in a scene.

    Args:
        scene: Input trimesh Scene.
        config: Conversion configuration.

    Returns:
        List of processed meshes with collision geometry.
    """
    processed = []

    # Get all geometry with their transforms
    for node_name in scene.graph.nodes_geometry:
        transform, geometry_name = scene.graph[node_name]
        geometry = scene.geometry[geometry_name]

        if isinstance(geometry, trimesh.Trimesh):
            # Create unique name
            name = f"{node_name}_{geometry_name}".replace(" ", "_").replace(".", "_")

            mesh_result = process_mesh(
                mesh=geometry,
                name=name,
                config=config,
                transform=transform,
            )
            processed.append(mesh_result)

    return processed
