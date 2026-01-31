"""Tests for mesh processing module."""

import tempfile
from pathlib import Path

import numpy as np
import pytest
import trimesh

from rebelai.mesh_processing import (
    load_mesh,
    process_mesh,
    process_scene,
)
from rebelai.types import CollisionMethod, ConversionConfig, ProcessedMesh


def create_simple_mesh() -> trimesh.Trimesh:
    """Create a simple box mesh for testing."""
    return trimesh.creation.box(extents=[1.0, 1.0, 1.0])


def create_concave_mesh() -> trimesh.Trimesh:
    """Create a concave L-shaped mesh for testing decomposition."""
    # Create an L-shape by combining two boxes
    box1 = trimesh.creation.box(extents=[1.0, 0.2, 1.0])
    box2 = trimesh.creation.box(extents=[0.2, 0.8, 1.0])
    box2.apply_translation([0.4, 0.5, 0])

    combined = trimesh.util.concatenate([box1, box2])
    return combined


class TestLoadMesh:
    """Tests for load_mesh function."""

    def test_load_glb(self):
        """Test loading GLB file."""
        mesh = create_simple_mesh()

        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
            mesh.export(f.name)
            scene = load_mesh(f.name)

        assert isinstance(scene, trimesh.Scene)
        assert len(scene.geometry) > 0

    def test_load_obj(self):
        """Test loading OBJ file."""
        mesh = create_simple_mesh()

        with tempfile.NamedTemporaryFile(suffix=".obj", delete=False) as f:
            mesh.export(f.name)
            scene = load_mesh(f.name)

        assert isinstance(scene, trimesh.Scene)

    def test_load_stl(self):
        """Test loading STL file."""
        mesh = create_simple_mesh()

        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as f:
            mesh.export(f.name)
            scene = load_mesh(f.name)

        assert isinstance(scene, trimesh.Scene)

    def test_load_from_bytes(self):
        """Test loading from bytes."""
        mesh = create_simple_mesh()

        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
            mesh.export(f.name)
            with open(f.name, "rb") as fh:
                data = fh.read()

        scene = load_mesh(data, file_type="glb")

        assert isinstance(scene, trimesh.Scene)

    def test_load_bytes_requires_filetype(self):
        """Test that loading bytes without file_type raises."""
        mesh = create_simple_mesh()

        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
            mesh.export(f.name)
            with open(f.name, "rb") as fh:
                data = fh.read()

        with pytest.raises(ValueError, match="file_type required"):
            load_mesh(data)

    def test_load_nonexistent_raises(self):
        """Test that loading nonexistent file raises."""
        with pytest.raises(ValueError, match="File not found"):
            load_mesh("/nonexistent/path/mesh.glb")


class TestProcessMesh:
    """Tests for process_mesh function."""

    def test_process_convex_hull(self):
        """Test processing with convex hull method."""
        mesh = create_simple_mesh()
        config = ConversionConfig(collision_method=CollisionMethod.CONVEX_HULL)

        result = process_mesh(mesh, "test", config)

        assert isinstance(result, ProcessedMesh)
        assert len(result.collision_geoms) == 1
        assert result.collision_geoms[0].geom_type == "mesh"

    def test_process_convex_decomposition(self):
        """Test processing with convex decomposition."""
        mesh = create_concave_mesh()
        config = ConversionConfig(collision_method=CollisionMethod.CONVEX_DECOMPOSITION)

        result = process_mesh(mesh, "test", config)

        assert isinstance(result, ProcessedMesh)
        assert len(result.collision_geoms) >= 1

    def test_process_bounding_box(self):
        """Test processing with bounding box."""
        mesh = create_simple_mesh()
        config = ConversionConfig(collision_method=CollisionMethod.BOUNDING_BOX)

        result = process_mesh(mesh, "test", config)

        assert isinstance(result, ProcessedMesh)
        assert len(result.collision_geoms) == 1
        assert result.collision_geoms[0].geom_type == "box"

    def test_process_primitives(self):
        """Test processing with primitives."""
        mesh = create_simple_mesh()
        config = ConversionConfig(collision_method=CollisionMethod.PRIMITIVES)

        result = process_mesh(mesh, "test", config)

        assert isinstance(result, ProcessedMesh)
        assert len(result.collision_geoms) == 1
        assert result.collision_geoms[0].geom_type == "box"

    def test_process_passthrough(self):
        """Test processing with passthrough."""
        mesh = create_simple_mesh()
        config = ConversionConfig(collision_method=CollisionMethod.PASSTHROUGH)

        result = process_mesh(mesh, "test", config)

        assert isinstance(result, ProcessedMesh)
        assert len(result.collision_geoms) == 1

    def test_process_with_transform(self):
        """Test processing with a transform."""
        mesh = create_simple_mesh()
        config = ConversionConfig(collision_method=CollisionMethod.CONVEX_HULL)

        # Create translation transform
        transform = np.eye(4)
        transform[:3, 3] = [1, 2, 3]

        result = process_mesh(mesh, "test", config, transform=transform)

        assert isinstance(result, ProcessedMesh)
        # Vertices should be transformed
        assert result.visual_vertices.mean(axis=0)[0] != 0

    def test_process_computes_mass(self):
        """Test that mass is computed from volume and density."""
        mesh = create_simple_mesh()  # 1x1x1 box, volume = 1
        config = ConversionConfig(density=1000.0)

        result = process_mesh(mesh, "test", config)

        # Mass should be approximately volume * density = 1000
        assert 900 < result.mass < 1100

    def test_process_with_simplification(self):
        """Test mesh simplification."""
        pytest.importorskip("fast_simplification")
        mesh = trimesh.creation.icosphere(subdivisions=4)  # High poly
        config = ConversionConfig(
            simplify=True,
            target_faces=100,
        )

        result = process_mesh(mesh, "test", config)

        assert isinstance(result, ProcessedMesh)


class TestProcessScene:
    """Tests for process_scene function."""

    def test_process_single_mesh_scene(self):
        """Test processing a scene with one mesh."""
        scene = trimesh.Scene()
        mesh = create_simple_mesh()
        scene.add_geometry(mesh, node_name="box")

        config = ConversionConfig()
        results = process_scene(scene, config)

        assert len(results) == 1
        assert isinstance(results[0], ProcessedMesh)

    def test_process_multi_mesh_scene(self):
        """Test processing a scene with multiple meshes."""
        scene = trimesh.Scene()

        box = create_simple_mesh()
        sphere = trimesh.creation.icosphere(radius=0.5)

        scene.add_geometry(box, node_name="box")
        scene.add_geometry(sphere, node_name="sphere")

        config = ConversionConfig()
        results = process_scene(scene, config)

        assert len(results) == 2

    def test_process_scene_preserves_transforms(self):
        """Test that scene transforms are applied."""
        scene = trimesh.Scene()

        box = create_simple_mesh()
        transform = np.eye(4)
        transform[:3, 3] = [5, 0, 0]  # Translate 5 units in X

        scene.add_geometry(box, node_name="box", transform=transform)

        config = ConversionConfig()
        results = process_scene(scene, config)

        assert len(results) == 1
        # Check that vertices are transformed
        mean_x = results[0].visual_vertices[:, 0].mean()
        assert mean_x > 4  # Should be around 5

    def test_process_empty_scene(self):
        """Test processing an empty scene."""
        scene = trimesh.Scene()
        config = ConversionConfig()

        results = process_scene(scene, config)

        assert len(results) == 0
