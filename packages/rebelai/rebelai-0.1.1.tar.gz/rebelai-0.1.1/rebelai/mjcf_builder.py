"""MJCF XML generation from processed meshes."""

import xml.etree.ElementTree as ET
from typing import Tuple

import numpy as np

from rebelai.types import CollisionGeom, ConversionConfig, ProcessedMesh


def _format_array(arr: np.ndarray | Tuple, precision: int = 6) -> str:
    """Format an array as a space-separated string."""
    if isinstance(arr, tuple):
        arr = np.array(arr)
    return " ".join(f"{v:.{precision}g}" for v in arr.flat)


def _mesh_to_inline_asset(
    name: str, vertices: np.ndarray, faces: np.ndarray
) -> Tuple[ET.Element, ET.Element]:
    """Create inline mesh asset elements.

    Returns vertex and face elements for the asset section.
    """
    vertex_name = f"{name}_vert"
    face_name = f"{name}_face"

    # Flatten vertices to string
    vert_data = _format_array(vertices.flatten())
    face_data = " ".join(str(int(f)) for f in faces.flatten())

    vertex_elem = ET.Element("mesh", name=name, vertex=vert_data, face=face_data)

    return vertex_elem


def _create_body_element(
    mesh: ProcessedMesh,
    config: ConversionConfig,
    body_id: int,
) -> Tuple[ET.Element, list[ET.Element]]:
    """Create a body element with geoms for a processed mesh.

    Returns:
        Tuple of (body element, list of mesh assets to add)
    """
    body = ET.Element("body", name=f"body_{mesh.name}")

    # Set position if not origin
    if any(p != 0 for p in mesh.position):
        body.set("pos", _format_array(mesh.position))

    # Set orientation if not identity
    if mesh.quaternion != (1.0, 0.0, 0.0, 0.0):
        body.set("quat", _format_array(mesh.quaternion))

    # Add inertial properties
    inertial = ET.SubElement(body, "inertial")
    inertial.set("mass", f"{mesh.mass:.6g}")
    inertial.set("pos", "0 0 0")
    # Approximate inertia as a sphere
    r_equiv = (mesh.mass / config.density * 3 / (4 * np.pi)) ** (1 / 3)
    inertia = 0.4 * mesh.mass * r_equiv**2
    inertial.set("diaginertia", f"{inertia:.6g} {inertia:.6g} {inertia:.6g}")

    # Add free joint for dynamics
    ET.SubElement(body, "freejoint", name=f"joint_{mesh.name}")

    mesh_assets = []

    # Add collision geoms
    for i, geom in enumerate(mesh.collision_geoms):
        geom_name = f"{mesh.name}_col_{i}"
        geom_elem = ET.SubElement(body, "geom")
        geom_elem.set("name", geom_name)
        geom_elem.set("type", geom.geom_type)
        geom_elem.set("rgba", "0.5 0.5 0.5 0.0")  # Invisible collision
        geom_elem.set("contype", "1")
        geom_elem.set("conaffinity", "1")
        geom_elem.set(
            "friction",
            f"{config.friction[0]} {config.friction[1]} {config.friction[2]}",
        )

        if geom.geom_type == "mesh" and len(geom.vertices) > 0:
            mesh_asset_name = f"mesh_{geom_name}"
            geom_elem.set("mesh", mesh_asset_name)
            mesh_asset = _mesh_to_inline_asset(
                mesh_asset_name, geom.vertices, geom.faces
            )
            mesh_assets.append(mesh_asset)
        elif geom.geom_type == "box":
            geom_elem.set("size", _format_array(geom.size))
            if any(p != 0 for p in geom.position):
                geom_elem.set("pos", _format_array(geom.position))
        elif geom.geom_type == "sphere":
            geom_elem.set("size", str(geom.size[0]))
        elif geom.geom_type == "cylinder":
            geom_elem.set("size", _format_array(geom.size[:2]))

    # Add visual geom
    visual_name = f"{mesh.name}_visual"
    visual_mesh_name = f"mesh_{visual_name}"
    visual_elem = ET.SubElement(body, "geom")
    visual_elem.set("name", visual_name)
    visual_elem.set("type", "mesh")
    visual_elem.set("mesh", visual_mesh_name)
    visual_elem.set("rgba", "0.8 0.8 0.8 1.0")
    visual_elem.set("contype", "0")
    visual_elem.set("conaffinity", "0")

    visual_asset = _mesh_to_inline_asset(
        visual_mesh_name, mesh.visual_vertices, mesh.visual_faces
    )
    mesh_assets.append(visual_asset)

    return body, mesh_assets


def build_mjcf(meshes: list[ProcessedMesh], config: ConversionConfig) -> str:
    """Build complete MJCF XML from processed meshes.

    Args:
        meshes: List of processed meshes.
        config: Conversion configuration.

    Returns:
        MJCF XML string.
    """
    # Root element
    mujoco = ET.Element("mujoco", model="rebelai_scene")

    # Compiler settings
    compiler = ET.SubElement(mujoco, "compiler")
    compiler.set("angle", "radian")
    compiler.set("coordinate", "local")
    compiler.set("meshdir", ".")

    # Options
    option = ET.SubElement(mujoco, "option")
    option.set("timestep", "0.002")
    option.set("gravity", "0 0 -9.81")
    option.set("integrator", "implicit")

    # Visual settings
    visual = ET.SubElement(mujoco, "visual")
    headlight = ET.SubElement(visual, "headlight")
    headlight.set("ambient", "0.4 0.4 0.4")
    headlight.set("diffuse", "0.8 0.8 0.8")

    # Default settings
    default = ET.SubElement(mujoco, "default")
    default_geom = ET.SubElement(default, "geom")
    default_geom.set(
        "friction",
        f"{config.friction[0]} {config.friction[1]} {config.friction[2]}",
    )

    # Asset section (populated as we process bodies)
    asset = ET.SubElement(mujoco, "asset")

    # Add texture and material for ground
    ET.SubElement(
        asset,
        "texture",
        name="grid",
        type="2d",
        builtin="checker",
        width="512",
        height="512",
        rgb1="0.2 0.2 0.2",
        rgb2="0.3 0.3 0.3",
    )
    ET.SubElement(
        asset,
        "material",
        name="grid_mat",
        texture="grid",
        texrepeat="8 8",
        reflectance="0.1",
    )

    # Worldbody
    worldbody = ET.SubElement(mujoco, "worldbody")

    # Add light
    ET.SubElement(
        worldbody,
        "light",
        name="main_light",
        pos="0 0 5",
        dir="0 0 -1",
        diffuse="1 1 1",
        specular="0.3 0.3 0.3",
    )

    # Add ground plane
    ET.SubElement(
        worldbody,
        "geom",
        name="ground",
        type="plane",
        size="10 10 0.1",
        material="grid_mat",
        contype="1",
        conaffinity="1",
    )

    # Process each mesh
    all_mesh_assets = []
    for i, mesh in enumerate(meshes):
        body_elem, mesh_assets = _create_body_element(mesh, config, i)
        worldbody.append(body_elem)
        all_mesh_assets.extend(mesh_assets)

    # Add all mesh assets
    for mesh_asset in all_mesh_assets:
        asset.append(mesh_asset)

    # Generate XML string
    ET.indent(mujoco, space="  ")
    xml_str = ET.tostring(mujoco, encoding="unicode")

    # Add XML declaration
    return f'<?xml version="1.0" encoding="utf-8"?>\n{xml_str}'
