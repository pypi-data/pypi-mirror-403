"""Low-level rendering primitives for crystal visualization.

This module contains functions for drawing atoms, bonds, unit cells,
coordination polyhedra, and other crystal visualization elements.
"""

from typing import Any

import numpy as np

from .data import AXIS_COLOURS, ELEMENT_COLOURS
from .projection import calculate_axis_origin, cell_to_vectors


def get_element_colour(symbol: str) -> str:
    """Get colour for an element.

    Args:
        symbol: Chemical element symbol

    Returns:
        Hex colour string
    """
    if symbol in ELEMENT_COLOURS:
        return ELEMENT_COLOURS[symbol]

    # Try ASE's jmol colours if available
    try:
        from ase.data import atomic_numbers
        from ase.data.colors import jmol_colors

        z = atomic_numbers[symbol]
        rgb = jmol_colors[z]
        return f"#{int(rgb[0] * 255):02x}{int(rgb[1] * 255):02x}{int(rgb[2] * 255):02x}"
    except (ImportError, KeyError, IndexError):
        return "#808080"  # Default grey


def get_element_radius(symbol: str) -> float:
    """Get display radius for an element.

    Args:
        symbol: Chemical element symbol

    Returns:
        Display radius in angstroms
    """
    try:
        from ase.data import atomic_numbers, covalent_radii

        z = atomic_numbers[symbol]
        return covalent_radii[z] * 0.5  # Scale down for display
    except (ImportError, KeyError, IndexError):
        return 0.5


def blend_colors(color1: str, color2: str) -> str:
    """Blend two hex colors to create a gradient midpoint.

    Args:
        color1: First hex colour
        color2: Second hex colour

    Returns:
        Blended hex colour
    """

    def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    blended = tuple((c1 + c2) // 2 for c1, c2 in zip(rgb1, rgb2, strict=False))
    return rgb_to_hex(blended)


def draw_unit_cell_box(ax: Any, cellpar: list[float], show_axes: bool = True) -> None:
    """Draw the unit cell box with optional axes.

    Args:
        ax: Matplotlib 3D axis
        cellpar: Cell parameters [a, b, c, alpha, beta, gamma]
        show_axes: Whether to draw crystallographic axes
    """
    va, vb, vc = cell_to_vectors(cellpar)

    # Define the 8 corners of the unit cell
    corners = np.array([[0, 0, 0], va, vb, vc, va + vb, va + vc, vb + vc, va + vb + vc])

    # Define the 12 edges
    edges = [
        [0, 1],
        [0, 2],
        [0, 3],  # From origin
        [1, 4],
        [1, 5],  # From a
        [2, 4],
        [2, 6],  # From b
        [3, 5],
        [3, 6],  # From c
        [4, 7],
        [5, 7],
        [6, 7],  # To opposite corner
    ]

    # Draw edges
    for i, j in edges:
        ax.plot3D(*zip(corners[i], corners[j], strict=False), "k-", linewidth=0.8, alpha=0.6)

    # Draw crystallographic axes
    if show_axes:
        axis_origin, axis_length = calculate_axis_origin(corners)

        # Normalize cell vectors for direction only
        va_dir = va / np.linalg.norm(va)
        vb_dir = vb / np.linalg.norm(vb)
        vc_dir = vc / np.linalg.norm(vc)

        for axis_name, direction in [("a", va_dir), ("b", vb_dir), ("c", vc_dir)]:
            ax.quiver(
                axis_origin[0],
                axis_origin[1],
                axis_origin[2],
                direction[0] * axis_length,
                direction[1] * axis_length,
                direction[2] * axis_length,
                color=AXIS_COLOURS[axis_name],
                arrow_length_ratio=0.1,
                linewidth=2,
            )
            text_pos = axis_origin + direction * axis_length * 1.08
            ax.text(
                text_pos[0],
                text_pos[1],
                text_pos[2],
                axis_name,
                fontsize=12,
                fontweight="bold",
                color=AXIS_COLOURS[axis_name],
            )


def draw_atoms(ax: Any, atoms: Any) -> None:
    """Draw atoms as spheres.

    Args:
        ax: Matplotlib 3D axis
        atoms: ASE Atoms object
    """
    positions = atoms.get_positions()
    symbols = atoms.get_chemical_symbols()

    for pos, sym in zip(positions, symbols, strict=False):
        colour = get_element_colour(sym)
        radius = get_element_radius(sym)

        # Create sphere
        u = np.linspace(0, 2 * np.pi, 20)
        v = np.linspace(0, np.pi, 10)
        x = radius * np.outer(np.cos(u), np.sin(v)) + pos[0]
        y = radius * np.outer(np.sin(u), np.sin(v)) + pos[1]
        z = radius * np.outer(np.ones(np.size(u)), np.cos(v)) + pos[2]

        ax.plot_surface(x, y, z, color=colour, alpha=0.9, linewidth=0)


def draw_bonds(ax: Any, atoms: Any, cutoff: float = 3.0) -> None:
    """Draw bonds between atoms within cutoff distance.

    Args:
        ax: Matplotlib 3D axis
        atoms: ASE Atoms object
        cutoff: Maximum bond length in Angstroms
    """
    positions = atoms.get_positions()
    symbols = atoms.get_chemical_symbols()
    n_atoms = len(atoms)

    # Find bonds using brute-force O(n^2)
    bonds = []
    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            dist = np.linalg.norm(positions[i] - positions[j])
            if dist < cutoff:
                bonds.append((i, j))

    # Draw each bond
    for i, j in bonds:
        color_i = get_element_colour(symbols[i])
        color_j = get_element_colour(symbols[j])
        midpoint = (positions[i] + positions[j]) / 2

        # First half (atom i to midpoint)
        ax.plot3D(
            [positions[i][0], midpoint[0]],
            [positions[i][1], midpoint[1]],
            [positions[i][2], midpoint[2]],
            color=color_i,
            linewidth=3.0,
            alpha=0.85,
            solid_capstyle="round",
        )
        # Second half (midpoint to atom j)
        ax.plot3D(
            [midpoint[0], positions[j][0]],
            [midpoint[1], positions[j][1]],
            [midpoint[2], positions[j][2]],
            color=color_j,
            linewidth=3.0,
            alpha=0.85,
            solid_capstyle="round",
        )


def draw_atom_labels(ax: Any, atoms: Any, offset: float = 0.35) -> None:
    """Draw element symbol labels on atoms.

    Args:
        ax: Matplotlib 3D axis
        atoms: ASE Atoms object
        offset: Distance to offset label from atom center
    """
    positions = atoms.get_positions()
    symbols = atoms.get_chemical_symbols()

    for pos, sym in zip(positions, symbols, strict=False):
        ax.text(
            pos[0] + offset * 0.5,
            pos[1] + offset * 0.5,
            pos[2] + offset,
            sym,
            fontsize=9,
            ha="center",
            va="bottom",
            fontweight="bold",
            color="#333333",
            bbox={
                "boxstyle": "round,pad=0.15",
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.7,
            },
        )


def draw_coordination_polyhedra(
    ax: Any, atoms: Any, center_element: str, coord_element: str, cutoff: float = 2.5
) -> None:
    """Draw coordination polyhedra around specified center atoms.

    Args:
        ax: Matplotlib 3D axis
        atoms: ASE Atoms object
        center_element: Element symbol for center atoms
        coord_element: Element symbol for coordinating atoms
        cutoff: Maximum distance for coordination
    """
    try:
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        from scipy.spatial import ConvexHull
    except ImportError:
        return

    positions = atoms.get_positions()
    symbols = atoms.get_chemical_symbols()

    center_indices = [i for i, s in enumerate(symbols) if s == center_element]
    coord_indices = [i for i, s in enumerate(symbols) if s == coord_element]

    if not center_indices or not coord_indices:
        return

    for center_idx in center_indices:
        center_pos = positions[center_idx]

        coord_atoms = []
        for coord_idx in coord_indices:
            dist = np.linalg.norm(positions[coord_idx] - center_pos)
            if 0 < dist < cutoff:
                coord_atoms.append(positions[coord_idx])

        if len(coord_atoms) >= 4:
            coord_array = np.array(coord_atoms)
            try:
                hull = ConvexHull(coord_array)
                faces = [coord_array[simplex] for simplex in hull.simplices]
                poly = Poly3DCollection(
                    faces, alpha=0.25, facecolor="#4FC3F7", edgecolor="#0288D1", linewidth=1.0
                )
                ax.add_collection3d(poly)
            except Exception:
                pass


def draw_legend(ax: Any, elements_used: set[str]) -> None:
    """Draw legend with colored dots for each element.

    Args:
        ax: Matplotlib axis
        elements_used: Set of element symbols present
    """
    y_pos = 0.95
    for symbol in sorted(elements_used):
        color = ELEMENT_COLOURS.get(symbol, "#808080")
        ax.text2D(
            0.02,
            y_pos,
            f"\u25cf {symbol}",
            transform=ax.transAxes,
            fontsize=11,
            color=color,
            fontweight="bold",
            bbox={
                "boxstyle": "round,pad=0.2",
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.8,
            },
        )
        y_pos -= 0.045


def draw_crystallographic_axes(
    ax: Any,
    axis_origin: np.ndarray,
    axis_length: float,
    directions: list[tuple[str, list[float]]] | None = None,
) -> None:
    """Draw crystallographic axes at the specified origin.

    Args:
        ax: Matplotlib 3D axis
        axis_origin: Origin point for axes
        axis_length: Length of axes
        directions: Optional list of (name, direction) tuples
    """
    if directions is None:
        directions = [("a", [1, 0, 0]), ("b", [0, 1, 0]), ("c", [0, 0, 1])]

    for axis_name, direction in directions:
        direction = np.array(direction)
        ax.quiver(
            axis_origin[0],
            axis_origin[1],
            axis_origin[2],
            direction[0] * axis_length,
            direction[1] * axis_length,
            direction[2] * axis_length,
            color=AXIS_COLOURS[axis_name],
            arrow_length_ratio=0.1,
            linewidth=2,
        )
        text_pos = axis_origin + direction * axis_length * 1.08
        ax.text(
            text_pos[0],
            text_pos[1],
            text_pos[2],
            axis_name,
            fontsize=14,
            fontweight="bold",
            color=AXIS_COLOURS[axis_name],
        )


def set_axes_equal(ax: Any) -> None:
    """Set 3D plot axes to equal scale.

    Args:
        ax: Matplotlib 3D axis
    """
    x_limits = ax.get_xlim3d()
    y_limits = ax.get_ylim3d()
    z_limits = ax.get_zlim3d()

    x_range = abs(x_limits[1] - x_limits[0])
    y_range = abs(y_limits[1] - y_limits[0])
    z_range = abs(z_limits[1] - z_limits[0])

    max_range = max(x_range, y_range, z_range)

    x_mid = np.mean(x_limits)
    y_mid = np.mean(y_limits)
    z_mid = np.mean(z_limits)

    ax.set_xlim3d([x_mid - max_range / 2, x_mid + max_range / 2])
    ax.set_ylim3d([y_mid - max_range / 2, y_mid + max_range / 2])
    ax.set_zlim3d([z_mid - max_range / 2, z_mid + max_range / 2])


def hide_axes_and_grid(ax: Any) -> None:
    """Hide the grid, panes, and axis lines for a clean visualization.

    Args:
        ax: Matplotlib 3D axis
    """
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor("none")
    ax.yaxis.pane.set_edgecolor("none")
    ax.zaxis.pane.set_edgecolor("none")
    ax.xaxis.line.set_color("none")
    ax.yaxis.line.set_color("none")
    ax.zaxis.line.set_color("none")
    ax.set_axis_off()
    ax.grid(False)
