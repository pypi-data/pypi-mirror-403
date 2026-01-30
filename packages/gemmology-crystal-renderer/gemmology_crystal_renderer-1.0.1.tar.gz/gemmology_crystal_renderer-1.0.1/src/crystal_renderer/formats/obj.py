"""
Wavefront OBJ export for crystal geometry.

Provides functions to export crystal geometry to the widely-supported
OBJ format for 3D visualization and modeling software.
"""

import numpy as np


def geometry_to_obj(
    vertices: np.ndarray,
    faces: list[list[int]],
    name: str = "crystal",
    face_normals: list[np.ndarray] | None = None,
    include_mtl: bool = True,
    face_colors: list[str] | None = None,
) -> tuple[str, str | None]:
    """Export crystal geometry to Wavefront OBJ format.

    Args:
        vertices: Nx3 array of vertex positions
        faces: List of faces, each face is a list of vertex indices
        name: Name for the object and material file
        face_normals: Optional list of face normal vectors
        include_mtl: Whether to generate a material file
        face_colors: Optional list of hex color strings for each face

    Returns:
        Tuple of (obj_content, mtl_content). mtl_content is None if
        include_mtl is False.
    """
    lines = [
        "# Wavefront OBJ export",
        f"# Crystal geometry: {name}",
        f"# Vertices: {len(vertices)}, Faces: {len(faces)}",
        "",
    ]

    if include_mtl:
        lines.append(f"mtllib {name}.mtl")
        lines.append("")

    # Export vertices
    lines.append("# Vertices")
    for v in vertices:
        lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
    lines.append("")

    # Export vertex normals if provided
    if face_normals:
        lines.append("# Vertex normals")
        for n in face_normals:
            n = np.asarray(n)
            lines.append(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}")
        lines.append("")

    # Export faces
    lines.append("# Faces")
    if include_mtl:
        lines.append("usemtl crystal_material")

    for i, face in enumerate(faces):
        # OBJ uses 1-based indexing
        if face_normals and i < len(face_normals):
            # Format: f v1//vn1 v2//vn2 ...
            indices = " ".join(f"{v + 1}//{i + 1}" for v in face)
        else:
            # Format: f v1 v2 v3 ...
            indices = " ".join(str(v + 1) for v in face)
        lines.append(f"f {indices}")

    obj_content = "\n".join(lines)

    # Generate material file
    mtl_content = None
    if include_mtl:
        mtl_lines = [
            f"# Material file for {name}",
            "",
            "newmtl crystal_material",
            "Ka 0.1 0.1 0.1",  # Ambient
            "Kd 0.8 0.8 0.9",  # Diffuse (light blue)
            "Ks 0.9 0.9 0.9",  # Specular
            "Ns 100.0",  # Specular exponent
            "d 0.9",  # Transparency (1 = opaque)
            "illum 2",  # Illumination model
        ]
        mtl_content = "\n".join(mtl_lines)

    return obj_content, mtl_content


def export_obj(
    vertices: np.ndarray,
    faces: list[list[int]],
    filepath: str,
    name: str | None = None,
    face_normals: list[np.ndarray] | None = None,
    include_mtl: bool = True,
) -> None:
    """Export crystal geometry to OBJ file.

    Args:
        vertices: Nx3 array of vertex positions
        faces: List of faces, each face is a list of vertex indices
        filepath: Output file path (should end with .obj)
        name: Optional name for the object (defaults to filename)
        face_normals: Optional list of face normal vectors
        include_mtl: Whether to write a companion .mtl file
    """
    import os

    if name is None:
        name = os.path.splitext(os.path.basename(filepath))[0]

    obj_content, mtl_content = geometry_to_obj(
        vertices=vertices,
        faces=faces,
        name=name,
        face_normals=face_normals,
        include_mtl=include_mtl,
    )

    # Write OBJ file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(obj_content)

    # Write MTL file if requested
    if include_mtl and mtl_content:
        mtl_path = os.path.splitext(filepath)[0] + ".mtl"
        with open(mtl_path, "w", encoding="utf-8") as f:
            f.write(mtl_content)


def geometry_to_obj_with_groups(
    vertices: np.ndarray,
    faces: list[list[int]],
    face_groups: list[int] | None = None,
    group_names: list[str] | None = None,
    name: str = "crystal",
    face_normals: list[np.ndarray] | None = None,
) -> tuple[str, str]:
    """Export geometry with face groups for multi-material rendering.

    Useful for twinned crystals where different components should
    have different materials/colors.

    Args:
        vertices: Nx3 array of vertex positions
        faces: List of faces
        face_groups: Component ID for each face (same length as faces)
        group_names: Optional names for each group
        name: Name for the object
        face_normals: Optional face normal vectors

    Returns:
        Tuple of (obj_content, mtl_content)
    """
    if face_groups is None:
        face_groups = [0] * len(faces)

    unique_groups = sorted(set(face_groups))
    n_groups = len(unique_groups)

    if group_names is None:
        group_names = [f"component_{i}" for i in unique_groups]

    # Color palette for groups
    colors = [
        (0.50, 0.83, 0.98),  # Light blue
        (1.00, 0.80, 0.50),  # Light orange
        (0.65, 0.84, 0.65),  # Light green
        (0.81, 0.58, 0.85),  # Light purple
        (0.94, 0.60, 0.60),  # Light red
        (0.56, 0.79, 0.98),  # Blue
    ]

    lines = [
        "# Wavefront OBJ export with face groups",
        f"# Crystal geometry: {name}",
        f"# Vertices: {len(vertices)}, Faces: {len(faces)}, Groups: {n_groups}",
        "",
        f"mtllib {name}.mtl",
        "",
    ]

    # Export vertices
    lines.append("# Vertices")
    for v in vertices:
        lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
    lines.append("")

    # Export normals
    if face_normals:
        lines.append("# Normals")
        for n in face_normals:
            n = np.asarray(n)
            lines.append(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}")
        lines.append("")

    # Export faces grouped by component
    lines.append("# Faces by group")
    group_to_idx = {g: i for i, g in enumerate(unique_groups)}

    for group in unique_groups:
        group_idx = group_to_idx[group]
        mat_name = f"material_{group_idx}"
        group_name = group_names[group_idx] if group_idx < len(group_names) else f"group_{group}"

        lines.append("")
        lines.append(f"g {group_name}")
        lines.append(f"usemtl {mat_name}")

        for face_idx, (face, fg) in enumerate(zip(faces, face_groups, strict=False)):
            if fg != group:
                continue

            if face_normals and face_idx < len(face_normals):
                indices = " ".join(f"{v + 1}//{face_idx + 1}" for v in face)
            else:
                indices = " ".join(str(v + 1) for v in face)
            lines.append(f"f {indices}")

    obj_content = "\n".join(lines)

    # Generate MTL with multiple materials
    mtl_lines = [
        f"# Material file for {name}",
        f"# {n_groups} materials",
        "",
    ]

    for i, _group in enumerate(unique_groups):
        color = colors[i % len(colors)]
        mtl_lines.extend(
            [
                f"newmtl material_{i}",
                f"Ka {color[0] * 0.1:.3f} {color[1] * 0.1:.3f} {color[2] * 0.1:.3f}",
                f"Kd {color[0]:.3f} {color[1]:.3f} {color[2]:.3f}",
                "Ks 0.9 0.9 0.9",
                "Ns 100.0",
                "d 0.85",
                "illum 2",
                "",
            ]
        )

    mtl_content = "\n".join(mtl_lines)

    return obj_content, mtl_content
