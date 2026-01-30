"""
GEMCAD format export for gem faceting software.

Provides functions to export crystal geometry to GEMCAD ASCII format,
used by GemCad, Gem Cut Studio, and similar faceting software.
"""

import math

import numpy as np


def geometry_to_gemcad(
    vertices: np.ndarray,
    faces: list[list[int]],
    face_normals: list[np.ndarray],
    name: str = "Crystal",
    ri: float = 1.54,
    gear: int = 96,
    system: str | None = None,
    face_millers: list[tuple[int, int, int]] | None = None,
) -> str:
    """Export crystal geometry to GEMCAD ASCII format.

    GEMCAD format specifies facets by elevation angle and index position,
    as used in gem cutting. This creates a representation suitable for
    faceting machines.

    Args:
        vertices: Nx3 array of vertex positions
        faces: List of faces, each face is a list of vertex indices
        face_normals: Normal vector for each face (required)
        name: Design name
        ri: Refractive index (default 1.54 for quartz)
        gear: Index gear size (commonly 96)
        system: Crystal system name (for comment)
        face_millers: Optional Miller indices for each face

    Returns:
        GEMCAD ASCII content as string
    """
    lines = [
        f"# GEMCAD design: {name}",
        "# Generated from crystal geometry",
    ]

    if system:
        lines.append(f"# Crystal system: {system}")

    lines.extend(
        [
            f"# Vertices: {len(vertices)}, Faces: {len(faces)}",
            "",
            f"gear {gear}",
            f"name {name}",
            f"ri {ri:.4f}",
            "",
        ]
    )

    # Determine symmetry based on face distribution
    symmetry = _detect_symmetry(face_normals)
    if symmetry:
        lines.append(f"s {symmetry}")
        lines.append("")

    # Facet definitions
    lines.append("# Facet definitions")
    lines.append("# Format: elevation_angle index [# Miller_index]")
    lines.append("")

    # Separate pavilion and crown facets
    pavilion_facets = []
    crown_facets = []

    for i, normal in enumerate(face_normals):
        normal = np.asarray(normal)
        normal = normal / np.linalg.norm(normal)

        # Calculate spherical coordinates
        x, y, z = normal

        # Elevation: angle from horizontal plane (0 = horizontal, 90 = vertical up)
        horizontal_dist = np.sqrt(x * x + y * y)
        elevation = math.degrees(math.atan2(abs(z), horizontal_dist))

        # Azimuth: angle around z axis from +x
        azimuth = math.degrees(math.atan2(y, x))
        if azimuth < 0:
            azimuth += 360

        # Convert azimuth to index position
        index = int(round((azimuth / 360) * gear)) % gear

        # Determine if pavilion (z < 0) or crown (z >= 0)
        is_pavilion = z < 0

        # Get Miller index if available
        miller_str = ""
        if face_millers and i < len(face_millers):
            miller = face_millers[i]
            miller_str = f"  # ({miller[0]} {miller[1]} {miller[2]})"

        facet_line = f"{elevation:6.2f} {index:02d}{miller_str}"

        if is_pavilion:
            pavilion_facets.append(("p", facet_line))
        else:
            crown_facets.append(("c", facet_line))

    # Write pavilion facets
    if pavilion_facets:
        lines.append("# Pavilion facets")
        for prefix, facet in pavilion_facets:
            lines.append(f"{prefix} {facet}")
        lines.append("")

    # Write crown facets
    if crown_facets:
        lines.append("# Crown facets")
        for prefix, facet in crown_facets:
            lines.append(f"{prefix} {facet}")
        lines.append("")

    lines.append("# End of facet data")

    return "\n".join(lines)


def export_gemcad(
    vertices: np.ndarray,
    faces: list[list[int]],
    face_normals: list[np.ndarray],
    filepath: str,
    name: str | None = None,
    ri: float = 1.54,
    gear: int = 96,
    system: str | None = None,
    face_millers: list[tuple[int, int, int]] | None = None,
) -> None:
    """Export crystal geometry to GEMCAD file.

    Args:
        vertices: Nx3 array of vertex positions
        faces: List of faces
        face_normals: Normal vector for each face
        filepath: Output file path (should end with .asc)
        name: Optional design name (defaults to filename)
        ri: Refractive index
        gear: Index gear size
        system: Crystal system name
        face_millers: Optional Miller indices
    """
    import os

    if name is None:
        name = os.path.splitext(os.path.basename(filepath))[0]

    content = geometry_to_gemcad(
        vertices=vertices,
        faces=faces,
        face_normals=face_normals,
        name=name,
        ri=ri,
        gear=gear,
        system=system,
        face_millers=face_millers,
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def _detect_symmetry(face_normals: list[np.ndarray]) -> str | None:
    """Detect symmetry from face normal distribution.

    Examines the distribution of face normals to infer crystal symmetry.

    Args:
        face_normals: List of face normal vectors

    Returns:
        GEMCAD symmetry code or None
    """
    if not face_normals:
        return None

    # Count faces by quadrant/octant to detect symmetry
    normals = [np.asarray(n) / np.linalg.norm(n) for n in face_normals]

    # Check for 6-fold symmetry (hexagonal)
    azimuth_counts: dict[int, int] = {}
    for n in normals:
        az = int(round(math.degrees(math.atan2(n[1], n[0])) / 60)) % 6
        azimuth_counts[az] = azimuth_counts.get(az, 0) + 1

    if len(azimuth_counts) >= 3 and all(c > 0 for c in azimuth_counts.values()):
        if len(set(azimuth_counts.values())) <= 2:
            return "6"

    # Check for 4-fold symmetry (tetragonal)
    azimuth_counts_4: dict[int, int] = {}
    for n in normals:
        az = int(round(math.degrees(math.atan2(n[1], n[0])) / 90)) % 4
        azimuth_counts_4[az] = azimuth_counts_4.get(az, 0) + 1

    if len(set(azimuth_counts_4.values())) <= 2:
        return "4"

    # Check for 3-fold symmetry (trigonal)
    azimuth_counts_3: dict[int, int] = {}
    for n in normals:
        az = int(round(math.degrees(math.atan2(n[1], n[0])) / 120)) % 3
        azimuth_counts_3[az] = azimuth_counts_3.get(az, 0) + 1

    if len(set(azimuth_counts_3.values())) <= 2:
        return "3"

    # Check for 2-fold with mirrors (orthorhombic)
    pos_x = sum(1 for n in normals if n[0] > 0.1)
    neg_x = sum(1 for n in normals if n[0] < -0.1)
    pos_y = sum(1 for n in normals if n[1] > 0.1)
    neg_y = sum(1 for n in normals if n[1] < -0.1)

    if abs(pos_x - neg_x) <= 1 and abs(pos_y - neg_y) <= 1:
        return "2m"

    # Check for simple mirror
    if abs(pos_x - neg_x) <= 1 or abs(pos_y - neg_y) <= 1:
        return "m"

    # No clear symmetry
    return "n"


# Refractive index reference values for common gems
GEMSTONE_RI: dict[str, float] = {
    "diamond": 2.417,
    "ruby": 1.770,
    "sapphire": 1.770,
    "corundum": 1.770,
    "emerald": 1.580,
    "beryl": 1.580,
    "aquamarine": 1.575,
    "quartz": 1.544,
    "amethyst": 1.544,
    "citrine": 1.544,
    "topaz": 1.630,
    "spinel": 1.718,
    "garnet": 1.760,
    "tourmaline": 1.640,
    "peridot": 1.690,
    "tanzanite": 1.700,
    "zircon": 1.950,
    "fluorite": 1.434,
}


def get_ri_for_gemstone(name: str) -> float:
    """Get refractive index for a gemstone.

    Args:
        name: Gemstone name (case-insensitive)

    Returns:
        Refractive index, or 1.54 (quartz) as default
    """
    return GEMSTONE_RI.get(name.lower(), 1.54)
