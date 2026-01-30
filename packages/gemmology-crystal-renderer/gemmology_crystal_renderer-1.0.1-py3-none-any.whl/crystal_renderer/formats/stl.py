"""STL (Stereolithography) export for crystal geometries.

This module provides functions to export crystal geometries to STL format
for 3D printing and CAD applications.
"""

import struct
from pathlib import Path

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


def calculate_triangle_normal(v0: np.ndarray, v1: np.ndarray, v2: np.ndarray) -> np.ndarray:
    """Calculate the normal vector for a triangle.

    Args:
        v0, v1, v2: Triangle vertex positions

    Returns:
        Unit normal vector
    """
    edge1 = v1 - v0
    edge2 = v2 - v0
    normal = np.cross(edge1, edge2)
    norm_len = np.linalg.norm(normal)
    if norm_len < 1e-10:
        return np.array([0.0, 0.0, 1.0])
    return normal / norm_len


def geometry_to_stl(vertices: np.ndarray, faces: list[list[int]], binary: bool = True) -> bytes:
    """Convert crystal geometry to STL format.

    Args:
        vertices: Nx3 array of vertex positions
        faces: List of faces (each face is a list of vertex indices)
        binary: If True, output binary STL; if False, output ASCII STL

    Returns:
        STL file content as bytes
    """
    # Triangulate all faces
    triangles = []
    for face in faces:
        triangles.extend(triangulate_face(vertices, face))

    if binary:
        return _geometry_to_binary_stl(vertices, triangles)
    else:
        return _geometry_to_ascii_stl(vertices, triangles).encode("ascii")


def _geometry_to_binary_stl(vertices: np.ndarray, triangles: list[tuple[int, int, int]]) -> bytes:
    """Generate binary STL content.

    Args:
        vertices: Vertex positions
        triangles: List of triangle vertex index tuples

    Returns:
        Binary STL data
    """
    # 80-byte header
    header = b"Crystal Geometry STL Export".ljust(80, b"\x00")

    # Number of triangles (4 bytes, little-endian)
    num_triangles = len(triangles)
    triangle_count = struct.pack("<I", num_triangles)

    # Triangle data
    triangle_data = []
    for t in triangles:
        v0, v1, v2 = vertices[t[0]], vertices[t[1]], vertices[t[2]]
        normal = calculate_triangle_normal(v0, v1, v2)

        # Normal vector (3 x float32)
        triangle_data.append(struct.pack("<fff", *normal))
        # Vertex 1 (3 x float32)
        triangle_data.append(struct.pack("<fff", *v0))
        # Vertex 2 (3 x float32)
        triangle_data.append(struct.pack("<fff", *v1))
        # Vertex 3 (3 x float32)
        triangle_data.append(struct.pack("<fff", *v2))
        # Attribute byte count (uint16, usually 0)
        triangle_data.append(struct.pack("<H", 0))

    return header + triangle_count + b"".join(triangle_data)


def _geometry_to_ascii_stl(vertices: np.ndarray, triangles: list[tuple[int, int, int]]) -> str:
    """Generate ASCII STL content.

    Args:
        vertices: Vertex positions
        triangles: List of triangle vertex index tuples

    Returns:
        ASCII STL string
    """
    lines = ["solid crystal"]

    for t in triangles:
        v0, v1, v2 = vertices[t[0]], vertices[t[1]], vertices[t[2]]
        normal = calculate_triangle_normal(v0, v1, v2)

        lines.append(f"  facet normal {normal[0]:.6e} {normal[1]:.6e} {normal[2]:.6e}")
        lines.append("    outer loop")
        lines.append(f"      vertex {v0[0]:.6e} {v0[1]:.6e} {v0[2]:.6e}")
        lines.append(f"      vertex {v1[0]:.6e} {v1[1]:.6e} {v1[2]:.6e}")
        lines.append(f"      vertex {v2[0]:.6e} {v2[1]:.6e} {v2[2]:.6e}")
        lines.append("    endloop")
        lines.append("  endfacet")

    lines.append("endsolid crystal")
    return "\n".join(lines)


def export_stl(
    vertices: np.ndarray, faces: list[list[int]], output_path: str | Path, binary: bool = True
) -> Path:
    """Export crystal geometry to an STL file.

    Args:
        vertices: Nx3 array of vertex positions
        faces: List of faces (each face is a list of vertex indices)
        output_path: Output file path
        binary: If True, output binary STL; if False, output ASCII STL

    Returns:
        Path to output file
    """
    output_path = Path(output_path)
    stl_data = geometry_to_stl(vertices, faces, binary)

    with open(output_path, "wb") as f:
        f.write(stl_data)

    return output_path
