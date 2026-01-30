"""3D projection utilities for crystal visualization.

This module handles 3D to 2D projection calculations, view transformations,
and visibility determination for crystal rendering.
"""

import numpy as np


def calculate_view_direction(elev: float, azim: float) -> np.ndarray:
    """Calculate view direction vector from elevation and azimuth angles.

    Args:
        elev: Elevation angle in degrees
        azim: Azimuth angle in degrees

    Returns:
        Unit vector pointing towards viewer
    """
    elev_rad = np.radians(elev)
    azim_rad = np.radians(azim)
    return np.array(
        [np.cos(elev_rad) * np.cos(azim_rad), np.cos(elev_rad) * np.sin(azim_rad), np.sin(elev_rad)]
    )


def calculate_axis_origin(
    vertices: np.ndarray, elev: float = 30, azim: float = -45, offset_factor: float = 0.02
) -> tuple[np.ndarray, float]:
    """Calculate axis placement for maximum crystal fill efficiency.

    Places axes at crystal corner with minimal clearance and adaptive length.
    The axes stay attached to the crystal's geometry in world coordinates.

    Args:
        vertices: Array of crystal vertex positions (N x 3)
        elev: Elevation angle (unused, kept for API compatibility)
        azim: Azimuth angle (unused, kept for API compatibility)
        offset_factor: Clearance from bounding box corner (0.02 = 2% typical)

    Returns:
        Tuple of (axis_origin, axis_length)
    """
    # Calculate bounding box
    min_bounds = np.min(vertices, axis=0)
    max_bounds = np.max(vertices, axis=0)
    extent = max_bounds - min_bounds
    max_extent = np.max(extent)

    # Place origin at front-bottom-left corner with tiny clearance (2%)
    axis_origin = np.array(
        [
            min_bounds[0] - max_extent * offset_factor,
            min_bounds[1] - max_extent * offset_factor,
            min_bounds[2] - max_extent * offset_factor * 0.5,
        ]
    )

    # Adaptive axis length: 25% base, capped per crystal dimension
    base_length = max_extent * 0.25
    min_length = max_extent * 0.18  # Minimum for visibility

    # Cap to 45% of smallest crystal dimension (prevents oversized axes)
    axis_length = max(min(base_length, np.min(extent) * 0.45), min_length)

    return axis_origin, axis_length


def calculate_vertex_visibility(
    vertices: np.ndarray, faces: list[list[int]], elev: float, azim: float, threshold: float = 0.1
) -> np.ndarray:
    """Determine which vertices are on front-facing vs back-facing surfaces.

    Args:
        vertices: Array of vertex positions (N x 3)
        faces: List of face vertex index arrays (each face is a list of indices)
        elev: Elevation angle in degrees
        azim: Azimuth angle in degrees
        threshold: Dot product threshold for front-facing (default 0.1)

    Returns:
        Boolean array, True for front-facing vertices
    """
    view_dir = calculate_view_direction(elev, azim)

    # Track which vertices are on at least one front-facing face
    vertex_front_facing = np.zeros(len(vertices), dtype=bool)

    for face in faces:
        face_indices = np.array(face)
        face_verts = vertices[face_indices]
        if len(face_verts) < 3:
            continue

        # Calculate face normal
        v1 = face_verts[1] - face_verts[0]
        v2 = face_verts[2] - face_verts[0]
        normal = np.cross(v1, v2)
        norm_len = np.linalg.norm(normal)
        if norm_len < 1e-10:
            continue
        normal = normal / norm_len

        # Check if face is front-facing
        if np.dot(normal, view_dir) > threshold:
            vertex_front_facing[face_indices] = True

    return vertex_front_facing


def calculate_face_normal(vertices: np.ndarray, face: list[int]) -> np.ndarray:
    """Calculate the normal vector for a face.

    Args:
        vertices: Array of all vertex positions
        face: List of vertex indices forming the face

    Returns:
        Unit normal vector, or zero vector if degenerate
    """
    if len(face) < 3:
        return np.zeros(3)

    face_verts = vertices[face]
    v1 = face_verts[1] - face_verts[0]
    v2 = face_verts[2] - face_verts[0]
    normal = np.cross(v1, v2)
    norm_len = np.linalg.norm(normal)

    if norm_len < 1e-10:
        return np.zeros(3)

    return normal / norm_len


def calculate_face_center(vertices: np.ndarray, face: list[int]) -> np.ndarray:
    """Calculate the center point of a face.

    Args:
        vertices: Array of all vertex positions
        face: List of vertex indices forming the face

    Returns:
        Center point as 3D vector
    """
    face_verts = vertices[face]
    return np.mean(face_verts, axis=0)


def is_face_visible(
    vertices: np.ndarray, face: list[int], elev: float, azim: float, threshold: float = 0.1
) -> bool:
    """Check if a face is visible from the given view angle.

    Args:
        vertices: Array of all vertex positions
        face: List of vertex indices forming the face
        elev: Elevation angle in degrees
        azim: Azimuth angle in degrees
        threshold: Dot product threshold for visibility

    Returns:
        True if face is front-facing
    """
    view_dir = calculate_view_direction(elev, azim)
    normal = calculate_face_normal(vertices, face)
    return np.dot(normal, view_dir) > threshold


def cell_to_vectors(cellpar: list[float]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Convert cell parameters to lattice vectors.

    Args:
        cellpar: [a, b, c, alpha, beta, gamma] cell parameters

    Returns:
        Tuple of (va, vb, vc) lattice vectors
    """
    a, b, c, alpha, beta, gamma = cellpar
    alpha_r = np.radians(alpha)
    beta_r = np.radians(beta)
    gamma_r = np.radians(gamma)

    # Vector a along x
    va = np.array([a, 0, 0])

    # Vector b in xy plane
    vb = np.array([b * np.cos(gamma_r), b * np.sin(gamma_r), 0])

    # Vector c
    cx = c * np.cos(beta_r)
    cy = c * (np.cos(alpha_r) - np.cos(beta_r) * np.cos(gamma_r)) / np.sin(gamma_r)
    cz = np.sqrt(max(0, c**2 - cx**2 - cy**2))  # Clamp to avoid negative sqrt
    vc = np.array([cx, cy, cz])

    return va, vb, vc


def calculate_bounding_box(vertices: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Calculate axis-aligned bounding box for vertices.

    Args:
        vertices: Array of vertex positions (N x 3)

    Returns:
        Tuple of (min_bounds, max_bounds) as 3D vectors
    """
    return np.min(vertices, axis=0), np.max(vertices, axis=0)


def calculate_view_bounds(
    vertices: np.ndarray,
    axis_origin: np.ndarray = None,
    axis_length: float = None,
    padding: float = 1.03,
) -> tuple[np.ndarray, float]:
    """Calculate view bounds that encompass all content with optional axes.

    Args:
        vertices: Array of vertex positions
        axis_origin: Optional axis origin point
        axis_length: Optional axis length
        padding: Padding factor (1.03 = 3% padding)

    Returns:
        Tuple of (center, half_extent) for setting axis limits
    """
    if axis_origin is not None and axis_length is not None:
        axis_tips = np.array(
            [
                axis_origin + np.array([axis_length * 1.08, 0, 0]),
                axis_origin + np.array([0, axis_length * 1.08, 0]),
                axis_origin + np.array([0, 0, axis_length * 1.08]),
            ]
        )
        all_points = np.vstack([vertices, axis_origin.reshape(1, 3), axis_tips])
    else:
        all_points = vertices

    content_min = np.min(all_points, axis=0)
    content_max = np.max(all_points, axis=0)
    center = (content_min + content_max) / 2
    content_extent = content_max - content_min
    half_extent = np.max(content_extent) / 2 * padding

    return center, half_extent
