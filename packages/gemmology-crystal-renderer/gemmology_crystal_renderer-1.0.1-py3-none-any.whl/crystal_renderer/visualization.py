"""High-level crystal visualization generators.

This module provides the main SVG generation functions for crystal
systems, CDL morphology, and combined views.
"""

from pathlib import Path
from typing import Any

# Import matplotlib with Agg backend for headless rendering
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# Internal imports
from .data import FORM_COLORS, HABIT_COLOURS
from .info_panel import render_info_panel
from .projection import (
    calculate_axis_origin,
    calculate_vertex_visibility,
    calculate_view_bounds,
)
from .rendering import (
    draw_crystallographic_axes,
    hide_axes_and_grid,
)


def generate_cdl_svg(
    cdl_string: str,
    output_path: str | Path,
    show_axes: bool = True,
    elev: float = 30,
    azim: float = -45,
    color_by_form: bool = False,
    show_grid: bool = True,
    face_labels: bool = False,
    info_properties: dict[str, Any] | None = None,
    info_position: str = "top-right",
    info_style: str = "compact",
    info_fontsize: int = 10,
    figsize: tuple[int, int] = (10, 10),
    dpi: int = 150,
) -> Path:
    """Generate SVG from Crystal Description Language notation.

    Args:
        cdl_string: CDL notation string (e.g., "cubic[m3m]:{111}@1.0 + {100}@1.3")
        output_path: Output SVG file path
        show_axes: Whether to show crystallographic axes
        elev: Elevation angle for view
        azim: Azimuth angle for view
        color_by_form: If True, color faces by which form they belong to
        show_grid: If False, hide background grid and panes
        face_labels: If True, show Miller indices on visible faces
        info_properties: Dictionary of properties to display in info panel
        info_position: Panel position
        info_style: Panel style ('compact', 'detailed', 'minimal')
        info_fontsize: Font size for info panel
        figsize: Figure size in inches
        dpi: Output resolution

    Returns:
        Path to output file
    """
    # Import CDL parser and geometry
    try:
        from cdl_parser import parse_cdl
        from crystal_geometry import cdl_to_geometry
    except ImportError as e:
        raise ImportError(
            "cdl-parser and crystal-geometry packages required. "
            "Install with: pip install cdl-parser crystal-geometry"
        ) from e

    output_path = Path(output_path)

    # Parse and generate geometry
    description = parse_cdl(cdl_string)
    geometry = cdl_to_geometry(description)

    # Get colours based on crystal system
    crystal_system = description.system
    default_colours = HABIT_COLOURS.get(crystal_system, HABIT_COLOURS["cubic"])

    # Create figure
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_proj_type("ortho")
    ax.view_init(elev=elev, azim=azim)

    # Draw faces
    if color_by_form:
        # Color each face by its form
        for i, face in enumerate(geometry.faces):
            verts = [geometry.vertices[j] for j in face]
            form_idx = geometry.face_forms[i] if i < len(geometry.face_forms) else 0
            colours = FORM_COLORS[form_idx % len(FORM_COLORS)]
            poly = Poly3DCollection(
                [verts],
                alpha=0.7,
                facecolor=colours["face"],
                edgecolor=colours["edge"],
                linewidth=1.5,
            )
            ax.add_collection3d(poly)
    else:
        # Use single color for all faces
        face_vertices = [[geometry.vertices[i] for i in face] for face in geometry.faces]
        poly = Poly3DCollection(
            face_vertices,
            alpha=0.7,
            facecolor=default_colours["face"],
            edgecolor=default_colours["edge"],
            linewidth=1.5,
        )
        ax.add_collection3d(poly)

    # Add vertices with depth-based visibility
    front_mask = calculate_vertex_visibility(geometry.vertices, geometry.faces, elev, azim)

    if np.any(front_mask):
        ax.scatter3D(
            geometry.vertices[front_mask, 0],
            geometry.vertices[front_mask, 1],
            geometry.vertices[front_mask, 2],
            color=default_colours["edge"],
            s=30,
            alpha=0.9,
            zorder=10,
        )

    back_mask = ~front_mask
    if np.any(back_mask):
        ax.scatter3D(
            geometry.vertices[back_mask, 0],
            geometry.vertices[back_mask, 1],
            geometry.vertices[back_mask, 2],
            color=default_colours["edge"],
            s=30,
            alpha=0.3,
            zorder=5,
        )

    # Add face labels if requested
    if face_labels and hasattr(geometry, "face_millers") and geometry.face_millers:
        _add_face_labels(ax, geometry, elev, azim)

    # Draw axes
    if show_axes:
        axis_origin, axis_length = calculate_axis_origin(geometry.vertices, elev, azim)
        draw_crystallographic_axes(ax, axis_origin, axis_length)

        # Calculate view bounds including axes
        center, half_extent = calculate_view_bounds(geometry.vertices, axis_origin, axis_length)
    else:
        center = np.array([0.0, 0.0, 0.0])
        half_extent = np.max(np.abs(geometry.vertices)) * 1.1

    # Set axis limits
    ax.set_xlim([center[0] - half_extent, center[0] + half_extent])
    ax.set_ylim([center[1] - half_extent, center[1] + half_extent])
    ax.set_zlim([center[2] - half_extent, center[2] + half_extent])

    # Hide grid if requested
    if not show_grid:
        hide_axes_and_grid(ax)

    # Create title from CDL
    forms_str = " + ".join(str(f.miller) for f in description.forms)
    title = f"{description.system.title()} [{description.point_group}] : {forms_str}"
    ax.set_title(title, fontsize=14, fontweight="bold")

    # Add legend for color-by-form mode
    if color_by_form and len(description.forms) > 1:
        _add_form_legend(ax, description.forms)

    # Clean up axes
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_zlabel("")
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_zticklabels([])

    # Render info panel
    if info_properties:
        render_info_panel(
            ax, info_properties, position=info_position, style=info_style, fontsize=info_fontsize
        )

    # Save
    plt.tight_layout()
    plt.savefig(output_path, format="svg", dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    return output_path


def generate_geometry_svg(
    vertices: np.ndarray,
    faces: list[list[int]],
    output_path: str | Path,
    face_normals: list[np.ndarray] | None = None,
    show_axes: bool = True,
    elev: float = 30,
    azim: float = -45,
    show_grid: bool = True,
    face_color: str = "#81D4FA",
    edge_color: str = "#0277BD",
    title: str | None = None,
    info_properties: dict[str, Any] | None = None,
    figsize: tuple[int, int] = (10, 10),
    dpi: int = 150,
) -> Path:
    """Generate SVG from raw geometry data.

    Args:
        vertices: Nx3 array of vertex positions
        faces: List of faces (each face is list of vertex indices)
        output_path: Output SVG file path
        face_normals: Optional list of face normal vectors
        show_axes: Whether to show crystallographic axes
        elev: Elevation angle for view
        azim: Azimuth angle for view
        show_grid: If False, hide background grid and panes
        face_color: Face fill color
        edge_color: Edge line color
        title: Optional title
        info_properties: Properties for info panel
        figsize: Figure size in inches
        dpi: Output resolution

    Returns:
        Path to output file
    """
    output_path = Path(output_path)
    vertices = np.asarray(vertices)

    # Create figure
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_proj_type("ortho")
    ax.view_init(elev=elev, azim=azim)

    # Draw faces
    face_vertices = [[vertices[i] for i in face] for face in faces]
    poly = Poly3DCollection(
        face_vertices, alpha=0.7, facecolor=face_color, edgecolor=edge_color, linewidth=1.5
    )
    ax.add_collection3d(poly)

    # Add vertices
    front_mask = calculate_vertex_visibility(vertices, faces, elev, azim)

    if np.any(front_mask):
        ax.scatter3D(
            vertices[front_mask, 0],
            vertices[front_mask, 1],
            vertices[front_mask, 2],
            color=edge_color,
            s=30,
            alpha=0.9,
            zorder=10,
        )

    back_mask = ~front_mask
    if np.any(back_mask):
        ax.scatter3D(
            vertices[back_mask, 0],
            vertices[back_mask, 1],
            vertices[back_mask, 2],
            color=edge_color,
            s=30,
            alpha=0.3,
            zorder=5,
        )

    # Draw axes
    if show_axes:
        axis_origin, axis_length = calculate_axis_origin(vertices, elev, azim)
        draw_crystallographic_axes(ax, axis_origin, axis_length)
        center, half_extent = calculate_view_bounds(vertices, axis_origin, axis_length)
    else:
        center = np.mean(vertices, axis=0)
        half_extent = np.max(np.abs(vertices - center)) * 1.2

    ax.set_xlim([center[0] - half_extent, center[0] + half_extent])
    ax.set_ylim([center[1] - half_extent, center[1] + half_extent])
    ax.set_zlim([center[2] - half_extent, center[2] + half_extent])

    if not show_grid:
        hide_axes_and_grid(ax)

    if title:
        ax.set_title(title, fontsize=14, fontweight="bold")

    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_zlabel("")
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_zticklabels([])

    if info_properties:
        render_info_panel(ax, info_properties)

    plt.tight_layout()
    plt.savefig(output_path, format="svg", dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    return output_path


def _add_face_labels(ax: Any, geometry: Any, elev: float, azim: float) -> None:
    """Add Miller index labels to visible faces."""
    from .projection import calculate_face_center, calculate_face_normal, calculate_view_direction

    view_dir = calculate_view_direction(elev, azim)

    for i, face in enumerate(geometry.faces):
        if i >= len(geometry.face_millers):
            continue

        center = calculate_face_center(geometry.vertices, face)
        normal = calculate_face_normal(geometry.vertices, face)

        if np.dot(normal, view_dir) > 0.1:
            miller = geometry.face_millers[i]
            label = f"({miller[0]}{miller[1]}{miller[2]})"
            ax.text(
                center[0],
                center[1],
                center[2],
                label,
                fontsize=8,
                ha="center",
                va="center",
                color="#333333",
                fontweight="bold",
                bbox={
                    "boxstyle": "round,pad=0.2",
                    "facecolor": "white",
                    "alpha": 0.7,
                    "edgecolor": "none",
                },
            )


def _add_form_legend(ax: Any, forms: list[Any]) -> None:
    """Add legend for color-by-form mode."""
    y_pos = 0.95
    for i, form in enumerate(forms):
        colours = FORM_COLORS[i % len(FORM_COLORS)]
        miller_str = str(form.miller)
        scale_str = f"@{form.scale}" if form.scale != 1.0 else ""
        ax.text2D(
            0.02,
            y_pos,
            f"\u25cf {miller_str}{scale_str}",
            transform=ax.transAxes,
            fontsize=11,
            color=colours["edge"],
            fontweight="bold",
            bbox={
                "boxstyle": "round,pad=0.2",
                "facecolor": colours["face"],
                "edgecolor": "none",
                "alpha": 0.8,
            },
        )
        y_pos -= 0.05
