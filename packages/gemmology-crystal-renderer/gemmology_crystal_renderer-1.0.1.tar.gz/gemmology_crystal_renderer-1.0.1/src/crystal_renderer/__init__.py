"""Crystal Renderer - SVG and 3D visualization for crystal geometries.

This package provides visualization tools for rendering crystal structures,
including SVG generation, format conversion, and 3D exports.

Example:
    >>> from crystal_renderer import generate_cdl_svg
    >>> generate_cdl_svg("cubic[m3m]:{111}@1.0", "octahedron.svg")

    >>> from crystal_renderer import export_stl, export_gltf
    >>> from crystal_geometry import create_octahedron
    >>> geom = create_octahedron()
    >>> export_stl(geom.vertices, geom.faces, "octahedron.stl")
"""

__version__ = "1.0.0"
__author__ = "Fabian Schuh"
__email__ = "fabian@gemmology.dev"

# High-level visualization
# Format conversion
from .conversion import (
    check_dependencies,
    convert_svg_to_raster,
    generate_with_format,
)

# Data and constants
from .data import (
    AXIS_COLOURS,
    CLEAVAGE_COLOUR,
    CRYSTAL_SYSTEMS,
    ELEMENT_COLOURS,
    FORM_COLORS,
    HABIT_COLOURS,
    TWIN_COLOURS,
)

# 3D format exports
from .formats import (
    export_gltf,
    export_stl,
    geometry_to_gltf,
    geometry_to_stl,
)

# Info panel
from .info_panel import (
    PROPERTY_LABELS,
    create_fga_info_panel,
    format_property_value,
    get_property_label,
    render_info_panel,
)

# Projection utilities
from .projection import (
    calculate_axis_origin,
    calculate_bounding_box,
    calculate_face_center,
    calculate_face_normal,
    calculate_vertex_visibility,
    calculate_view_bounds,
    calculate_view_direction,
    cell_to_vectors,
    is_face_visible,
)

# Rendering primitives
from .rendering import (
    blend_colors,
    draw_atom_labels,
    draw_atoms,
    draw_bonds,
    draw_coordination_polyhedra,
    draw_crystallographic_axes,
    draw_legend,
    draw_unit_cell_box,
    get_element_colour,
    get_element_radius,
    hide_axes_and_grid,
    set_axes_equal,
)
from .visualization import (
    generate_cdl_svg,
    generate_geometry_svg,
)

__all__ = [
    # Version
    "__version__",
    # High-level visualization
    "generate_cdl_svg",
    "generate_geometry_svg",
    # Constants
    "AXIS_COLOURS",
    "ELEMENT_COLOURS",
    "CRYSTAL_SYSTEMS",
    "HABIT_COLOURS",
    "FORM_COLORS",
    "TWIN_COLOURS",
    "CLEAVAGE_COLOUR",
    "PROPERTY_LABELS",
    # Projection
    "calculate_axis_origin",
    "calculate_vertex_visibility",
    "calculate_view_direction",
    "calculate_face_normal",
    "calculate_face_center",
    "is_face_visible",
    "cell_to_vectors",
    "calculate_bounding_box",
    "calculate_view_bounds",
    # Rendering
    "get_element_colour",
    "get_element_radius",
    "blend_colors",
    "draw_unit_cell_box",
    "draw_atoms",
    "draw_bonds",
    "draw_atom_labels",
    "draw_coordination_polyhedra",
    "draw_legend",
    "draw_crystallographic_axes",
    "set_axes_equal",
    "hide_axes_and_grid",
    # Info panel
    "render_info_panel",
    "create_fga_info_panel",
    "get_property_label",
    "format_property_value",
    # Conversion
    "convert_svg_to_raster",
    "generate_with_format",
    "check_dependencies",
    # 3D exports
    "export_stl",
    "geometry_to_stl",
    "export_gltf",
    "geometry_to_gltf",
]
