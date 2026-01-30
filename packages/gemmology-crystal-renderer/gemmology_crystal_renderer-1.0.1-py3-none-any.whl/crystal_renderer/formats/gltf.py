"""glTF (GL Transmission Format) export for crystal geometries.

This module provides functions to export crystal geometries to glTF format
for web, AR, and 3D viewer applications.
"""

import base64
import json
from pathlib import Path
from typing import Any

import numpy as np


def triangulate_face(vertices: np.ndarray, face: list[int]) -> list[tuple[int, int, int]]:
    """Triangulate a polygon face using fan triangulation.

    Args:
        vertices: Array of all vertex positions
        face: List of vertex indices forming the face

    Returns:
        List of triangle tuples (v0, v1, v2)
    """
    if len(face) < 3:
        return []

    triangles = []
    v0 = face[0]
    for i in range(1, len(face) - 1):
        triangles.append((v0, face[i], face[i + 1]))

    return triangles


def calculate_vertex_normals(vertices: np.ndarray, faces: list[list[int]]) -> np.ndarray:
    """Calculate per-vertex normals by averaging face normals.

    Args:
        vertices: Nx3 array of vertex positions
        faces: List of faces

    Returns:
        Nx3 array of vertex normals
    """
    normals = np.zeros_like(vertices)

    for face in faces:
        if len(face) < 3:
            continue

        # Calculate face normal
        v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
        edge1 = v1 - v0
        edge2 = v2 - v0
        face_normal = np.cross(edge1, edge2)
        norm_len = np.linalg.norm(face_normal)
        if norm_len > 1e-10:
            face_normal = face_normal / norm_len

            # Add to all vertices of the face
            for idx in face:
                normals[idx] += face_normal

    # Normalize
    norms = np.linalg.norm(normals, axis=1, keepdims=True)
    norms[norms < 1e-10] = 1.0
    normals = normals / norms

    return normals


def geometry_to_gltf(
    vertices: np.ndarray,
    faces: list[list[int]],
    color: tuple[float, float, float, float] | None = None,
    name: str = "crystal",
) -> dict[str, Any]:
    """Convert crystal geometry to glTF format.

    Args:
        vertices: Nx3 array of vertex positions
        faces: List of faces (each face is a list of vertex indices)
        color: Optional RGBA color tuple (0-1 range)
        name: Mesh name

    Returns:
        glTF JSON structure
    """
    # Triangulate all faces
    triangles = []
    for face in faces:
        triangles.extend(triangulate_face(vertices, face))

    if not triangles:
        raise ValueError("No valid triangles generated from faces")

    # Calculate normals
    normals = calculate_vertex_normals(vertices, faces)

    # Build index buffer
    indices = np.array(triangles, dtype=np.uint16).flatten()

    # Convert to float32
    positions = vertices.astype(np.float32)
    normals = normals.astype(np.float32)

    # Create binary buffer
    position_bytes = positions.tobytes()
    normal_bytes = normals.tobytes()
    index_bytes = indices.tobytes()

    # Pad to 4-byte boundary
    def pad_to_4(data: bytes) -> bytes:
        padding = (4 - len(data) % 4) % 4
        return data + b"\x00" * padding

    position_bytes = pad_to_4(position_bytes)
    normal_bytes = pad_to_4(normal_bytes)
    index_bytes = pad_to_4(index_bytes)

    buffer_data = position_bytes + normal_bytes + index_bytes
    buffer_uri = "data:application/octet-stream;base64," + base64.b64encode(buffer_data).decode(
        "ascii"
    )

    # Calculate bounds
    min_pos = positions.min(axis=0).tolist()
    max_pos = positions.max(axis=0).tolist()

    # Build glTF structure
    gltf = {
        "asset": {"version": "2.0", "generator": "crystal-renderer"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": name}],
        "meshes": [
            {
                "name": name,
                "primitives": [
                    {"attributes": {"POSITION": 0, "NORMAL": 1}, "indices": 2, "material": 0}
                ],
            }
        ],
        "accessors": [
            {
                "bufferView": 0,
                "byteOffset": 0,
                "componentType": 5126,  # FLOAT
                "count": len(vertices),
                "type": "VEC3",
                "min": min_pos,
                "max": max_pos,
            },
            {
                "bufferView": 1,
                "byteOffset": 0,
                "componentType": 5126,  # FLOAT
                "count": len(vertices),
                "type": "VEC3",
            },
            {
                "bufferView": 2,
                "byteOffset": 0,
                "componentType": 5123,  # UNSIGNED_SHORT
                "count": len(indices),
                "type": "SCALAR",
            },
        ],
        "bufferViews": [
            {
                "buffer": 0,
                "byteOffset": 0,
                "byteLength": len(position_bytes),
                "target": 34962,  # ARRAY_BUFFER
            },
            {
                "buffer": 0,
                "byteOffset": len(position_bytes),
                "byteLength": len(normal_bytes),
                "target": 34962,  # ARRAY_BUFFER
            },
            {
                "buffer": 0,
                "byteOffset": len(position_bytes) + len(normal_bytes),
                "byteLength": len(index_bytes),
                "target": 34963,  # ELEMENT_ARRAY_BUFFER
            },
        ],
        "buffers": [{"byteLength": len(buffer_data), "uri": buffer_uri}],
        "materials": [
            {
                "name": "crystal_material",
                "pbrMetallicRoughness": {
                    "baseColorFactor": list(color) if color else [0.5, 0.7, 0.9, 0.8],
                    "metallicFactor": 0.1,
                    "roughnessFactor": 0.3,
                },
                "alphaMode": "BLEND" if (color and color[3] < 1.0) else "OPAQUE",
            }
        ],
    }

    return gltf


def export_gltf(
    vertices: np.ndarray,
    faces: list[list[int]],
    output_path: str | Path,
    color: tuple[float, float, float, float] | None = None,
    name: str = "crystal",
) -> Path:
    """Export crystal geometry to a glTF file.

    Args:
        vertices: Nx3 array of vertex positions
        faces: List of faces (each face is a list of vertex indices)
        output_path: Output file path
        color: Optional RGBA color tuple (0-1 range)
        name: Mesh name

    Returns:
        Path to output file
    """
    output_path = Path(output_path)
    gltf = geometry_to_gltf(vertices, faces, color, name)

    with open(output_path, "w") as f:
        json.dump(gltf, f, indent=2)

    return output_path
