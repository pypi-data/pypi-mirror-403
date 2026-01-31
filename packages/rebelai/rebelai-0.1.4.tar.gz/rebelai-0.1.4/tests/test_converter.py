"""End-to-end tests for the converter module."""

import tempfile
from pathlib import Path

import mujoco
import numpy as np
import pytest
import trimesh

import rebelai
from rebelai import CollisionMethod, ConversionConfig
from rebelai.converter import to_mjcf


def create_test_mesh(filename: str) -> Path:
    """Create a simple test mesh file."""
    # Create a simple box mesh
    box = trimesh.creation.box(extents=[1.0, 1.0, 1.0])

    tmpdir = tempfile.mkdtemp()
    filepath = Path(tmpdir) / filename
    box.export(filepath)
    return filepath


def create_complex_test_scene(filename: str) -> Path:
    """Create a test scene with multiple objects."""
    scene = trimesh.Scene()

    # Add a box
    box = trimesh.creation.box(extents=[1.0, 1.0, 1.0])
    box.apply_translation([0, 0, 0.5])
    scene.add_geometry(box, node_name="box")

    # Add a sphere
    sphere = trimesh.creation.icosphere(radius=0.3)
    sphere.apply_translation([2, 0, 0.3])
    scene.add_geometry(sphere, node_name="sphere")

    # Add a cylinder
    cylinder = trimesh.creation.cylinder(radius=0.2, height=1.0)
    cylinder.apply_translation([-2, 0, 0.5])
    scene.add_geometry(cylinder, node_name="cylinder")

    tmpdir = tempfile.mkdtemp()
    filepath = Path(tmpdir) / filename
    scene.export(filepath)
    return filepath


class TestLoad:
    """Tests for the load() function."""

    def test_load_glb_file(self):
        """Test loading a GLB file."""
        filepath = create_test_mesh("test.glb")

        model = rebelai.load(filepath)

        assert isinstance(model, mujoco.MjModel)
        assert model.ngeom > 0

    def test_load_obj_file(self):
        """Test loading an OBJ file."""
        filepath = create_test_mesh("test.obj")

        model = rebelai.load(filepath)

        assert isinstance(model, mujoco.MjModel)
        assert model.ngeom > 0

    def test_load_stl_file(self):
        """Test loading an STL file."""
        filepath = create_test_mesh("test.stl")

        model = rebelai.load(filepath)

        assert isinstance(model, mujoco.MjModel)
        assert model.ngeom > 0

    def test_load_with_default_config(self):
        """Test loading with default configuration."""
        filepath = create_test_mesh("test.glb")

        model = rebelai.load(filepath)

        assert isinstance(model, mujoco.MjModel)

    def test_load_with_custom_config(self):
        """Test loading with custom configuration."""
        filepath = create_test_mesh("test.glb")

        config = ConversionConfig(
            collision_method=CollisionMethod.CONVEX_HULL,
            density=500.0,
            friction=(0.5, 0.01, 0.001),
        )
        model = rebelai.load(filepath, config=config)

        assert isinstance(model, mujoco.MjModel)

    def test_load_from_bytes(self):
        """Test loading from bytes."""
        filepath = create_test_mesh("test.glb")

        with open(filepath, "rb") as f:
            data = f.read()

        model = rebelai.load(data, file_type="glb")

        assert isinstance(model, mujoco.MjModel)

    def test_load_nonexistent_file_raises(self):
        """Test that loading nonexistent file raises ValueError."""
        with pytest.raises(ValueError, match="File not found"):
            rebelai.load("/nonexistent/path/file.glb")

    def test_load_bytes_without_filetype_raises(self):
        """Test that loading bytes without file_type raises ValueError."""
        filepath = create_test_mesh("test.glb")

        with open(filepath, "rb") as f:
            data = f.read()

        with pytest.raises(ValueError, match="file_type required"):
            rebelai.load(data)


class TestCollisionMethods:
    """Tests for different collision methods."""

    def test_convex_hull(self):
        """Test convex hull collision method."""
        filepath = create_test_mesh("test.glb")
        config = ConversionConfig(collision_method=CollisionMethod.CONVEX_HULL)

        model = rebelai.load(filepath, config=config)

        assert isinstance(model, mujoco.MjModel)

    def test_convex_decomposition(self):
        """Test convex decomposition collision method."""
        filepath = create_test_mesh("test.glb")
        config = ConversionConfig(collision_method=CollisionMethod.CONVEX_DECOMPOSITION)

        model = rebelai.load(filepath, config=config)

        assert isinstance(model, mujoco.MjModel)

    def test_bounding_box(self):
        """Test bounding box collision method."""
        filepath = create_test_mesh("test.glb")
        config = ConversionConfig(collision_method=CollisionMethod.BOUNDING_BOX)

        model = rebelai.load(filepath, config=config)

        assert isinstance(model, mujoco.MjModel)

    def test_primitives(self):
        """Test primitives collision method."""
        filepath = create_test_mesh("test.glb")
        config = ConversionConfig(collision_method=CollisionMethod.PRIMITIVES)

        model = rebelai.load(filepath, config=config)

        assert isinstance(model, mujoco.MjModel)

    def test_passthrough(self):
        """Test passthrough collision method (for convex meshes)."""
        filepath = create_test_mesh("test.glb")
        config = ConversionConfig(collision_method=CollisionMethod.PASSTHROUGH)

        model = rebelai.load(filepath, config=config)

        assert isinstance(model, mujoco.MjModel)


class TestSimulation:
    """Tests that verify MuJoCo simulation works."""

    def test_basic_simulation(self):
        """Test that simulation runs without errors."""
        filepath = create_test_mesh("test.glb")
        model = rebelai.load(filepath)

        data = mujoco.MjData(model)

        # Run simulation for 100 steps
        for _ in range(100):
            mujoco.mj_step(model, data)

        # Object should have fallen due to gravity
        # (z position should have decreased from initial)

    def test_simulation_with_multiple_objects(self):
        """Test simulation with multiple objects."""
        filepath = create_complex_test_scene("test_scene.glb")
        model = rebelai.load(filepath)

        data = mujoco.MjData(model)

        # Run simulation
        for _ in range(100):
            mujoco.mj_step(model, data)

    def test_collision_detection(self):
        """Test that collision detection works."""
        filepath = create_test_mesh("test.glb")
        model = rebelai.load(filepath)

        data = mujoco.MjData(model)

        # Run until object hits ground
        for _ in range(1000):
            mujoco.mj_step(model, data)
            if data.ncon > 0:  # Contact detected
                break

        # Should have detected contact with ground
        assert data.ncon > 0


class TestToMjcf:
    """Tests for the to_mjcf() function."""

    def test_to_mjcf_returns_xml(self):
        """Test that to_mjcf returns valid XML."""
        filepath = create_test_mesh("test.glb")

        xml = to_mjcf(filepath)

        assert isinstance(xml, str)
        assert xml.startswith('<?xml')
        assert '<mujoco' in xml
        assert '</mujoco>' in xml

    def test_to_mjcf_contains_mesh_data(self):
        """Test that generated XML contains mesh data."""
        filepath = create_test_mesh("test.glb")

        xml = to_mjcf(filepath)

        assert '<mesh' in xml
        assert 'vertex=' in xml
        assert 'face=' in xml


class TestConfig:
    """Tests for ConversionConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ConversionConfig()

        assert config.collision_method == CollisionMethod.CONVEX_DECOMPOSITION
        assert config.coacd_threshold == 0.05
        assert config.density == 1000.0
        assert config.friction == (1.0, 0.005, 0.0001)

    def test_custom_config(self):
        """Test custom configuration."""
        config = ConversionConfig(
            collision_method=CollisionMethod.CONVEX_HULL,
            coacd_threshold=0.1,
            density=500.0,
            friction=(0.5, 0.01, 0.001),
        )

        assert config.collision_method == CollisionMethod.CONVEX_HULL
        assert config.coacd_threshold == 0.1
        assert config.density == 500.0
        assert config.friction == (0.5, 0.01, 0.001)


# Note: These tests require mocking since they involve the World Labs API
# Run with: pytest tests/test_converter.py::TestGenerate -v
try:
    from unittest.mock import MagicMock, patch
    from rebelai.converter import generate
    from rebelai.worldlabs import GenerationResult

    class TestGenerate:
        """Tests for the generate() function."""

        @patch("rebelai.converter.generate_mesh")
        def test_generate_calls_worldlabs_api(self, mock_generate_mesh):
            """Test that generate() calls the World Labs API."""
            # Create a real GLB file for the mock to return
            box = trimesh.creation.box(extents=[1.0, 1.0, 1.0])
            with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
                box.export(f.name)
                with open(f.name, "rb") as glb_file:
                    glb_data = glb_file.read()

            mock_generate_mesh.return_value = GenerationResult(
                job_id="job_123",
                status="completed",
                mesh_url="https://cdn.worldlabs.ai/mesh.glb",
                mesh_data=glb_data,
                file_type="glb",
            )

            model = generate("kitchen table", api_key="wl_test")

            assert isinstance(model, mujoco.MjModel)
            mock_generate_mesh.assert_called_once()
            call_kwargs = mock_generate_mesh.call_args[1]
            assert call_kwargs["prompt"] == "kitchen table"
            assert call_kwargs["api_key"] == "wl_test"

        @patch("rebelai.converter.generate_mesh")
        def test_generate_passes_config(self, mock_generate_mesh):
            """Test that generate() passes config to load()."""
            box = trimesh.creation.box(extents=[1.0, 1.0, 1.0])
            with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
                box.export(f.name)
                with open(f.name, "rb") as glb_file:
                    glb_data = glb_file.read()

            mock_generate_mesh.return_value = GenerationResult(
                job_id="job_123",
                status="completed",
                mesh_data=glb_data,
                file_type="glb",
            )

            config = ConversionConfig(
                collision_method=CollisionMethod.CONVEX_HULL,
                density=500.0,
            )

            model = generate("test", api_key="wl_test", config=config)

            assert isinstance(model, mujoco.MjModel)

        @patch("rebelai.converter.generate_mesh")
        def test_generate_passes_quality_options(self, mock_generate_mesh):
            """Test that generate() passes quality and style options."""
            box = trimesh.creation.box(extents=[1.0, 1.0, 1.0])
            with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
                box.export(f.name)
                with open(f.name, "rb") as glb_file:
                    glb_data = glb_file.read()

            mock_generate_mesh.return_value = GenerationResult(
                job_id="job_123",
                status="completed",
                mesh_data=glb_data,
                file_type="glb",
            )

            generate(
                "test",
                api_key="wl_test",
                quality="high",
                style="realistic",
                poll_interval=5.0,
                max_wait=300.0,
            )

            call_kwargs = mock_generate_mesh.call_args[1]
            assert call_kwargs["quality"] == "high"
            assert call_kwargs["style"] == "realistic"
            assert call_kwargs["poll_interval"] == 5.0
            assert call_kwargs["max_wait"] == 300.0

except ImportError:
    # Skip if mujoco not available
    pass
