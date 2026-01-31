"""Type definitions for RebelAI."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple

import numpy as np


class CollisionMethod(Enum):
    """Methods for generating collision geometry from visual meshes."""

    CONVEX_HULL = "convex_hull"
    """Single convex hull wrapping the entire mesh. Fast but imprecise for concave objects."""

    CONVEX_DECOMPOSITION = "convex_decomposition"
    """Decompose into multiple convex hulls using CoACD. Best for complex shapes."""

    BOUNDING_BOX = "bounding_box"
    """Axis-aligned bounding box. Fastest but least accurate."""

    PRIMITIVES = "primitives"
    """Fit geometric primitives (box, sphere, cylinder). Good for simple objects."""

    PASSTHROUGH = "passthrough"
    """Use mesh directly as collision geometry. Only works for convex meshes in MuJoCo."""


@dataclass
class ConversionConfig:
    """Configuration for mesh to physics conversion.

    Attributes:
        collision_method: Method to generate collision geometry.
        coacd_threshold: CoACD decomposition quality threshold (0-1).
            Lower values produce more accurate but more numerous hulls.
        coacd_max_convex_hull: Maximum number of convex hulls from decomposition.
        density: Default density in kg/m^3 for mass calculation.
        friction: MuJoCo friction parameters (slide, spin, roll).
        simplify: Whether to simplify meshes before processing.
        target_faces: Target face count when simplifying.
        merge_threshold: Distance threshold for merging nearby vertices.
    """

    collision_method: CollisionMethod = CollisionMethod.CONVEX_DECOMPOSITION
    coacd_threshold: float = 0.05
    coacd_max_convex_hull: int = 32
    density: float = 1000.0
    friction: Tuple[float, float, float] = (1.0, 0.005, 0.0001)
    simplify: bool = False
    target_faces: int = 1000
    merge_threshold: float = 1e-6


@dataclass
class CollisionGeom:
    """Internal representation of a collision geometry.

    Attributes:
        name: Unique identifier for this geometry.
        vertices: Nx3 array of vertex positions.
        faces: Mx3 array of face indices.
        position: Position offset (x, y, z).
        quaternion: Orientation as quaternion (w, x, y, z).
        geom_type: MuJoCo geom type ('mesh', 'box', 'sphere', 'cylinder').
        size: Size parameters for primitive types.
    """

    name: str
    vertices: np.ndarray
    faces: np.ndarray
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    quaternion: Tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0)
    geom_type: str = "mesh"
    size: Tuple[float, ...] = field(default_factory=tuple)


@dataclass
class ProcessedMesh:
    """A processed mesh ready for MJCF generation.

    Attributes:
        name: Name of the original mesh/node.
        visual_vertices: Vertices for visual rendering.
        visual_faces: Faces for visual rendering.
        collision_geoms: List of collision geometries.
        position: World position.
        quaternion: World orientation (w, x, y, z).
        mass: Computed mass based on volume and density.
    """

    name: str
    visual_vertices: np.ndarray
    visual_faces: np.ndarray
    collision_geoms: list[CollisionGeom]
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    quaternion: Tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0)
    mass: float = 1.0
