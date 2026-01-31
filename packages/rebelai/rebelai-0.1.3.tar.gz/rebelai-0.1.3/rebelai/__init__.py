"""RebelAI - Convert visual meshes to physics-ready MuJoCo models."""

from rebelai.converter import generate, load, load_from_file, to_mjcf
from rebelai.types import CollisionMethod, ConversionConfig
from rebelai.worldlabs import (
    WorldLabsAPIError,
    WorldLabsAuthError,
    WorldLabsError,
    WorldLabsTimeoutError,
)

__version__ = "0.1.3"
__all__ = [
    # Core functions
    "generate",
    "load",
    "load_from_file",
    "to_mjcf",
    # Configuration
    "ConversionConfig",
    "CollisionMethod",
    # Exceptions
    "WorldLabsError",
    "WorldLabsAuthError",
    "WorldLabsAPIError",
    "WorldLabsTimeoutError",
]
