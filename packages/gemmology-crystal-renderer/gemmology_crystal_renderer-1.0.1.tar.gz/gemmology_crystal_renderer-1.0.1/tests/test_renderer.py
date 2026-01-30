"""
Test suite for crystal-renderer.

Tests rendering functions, format exports, and visualization.
"""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from crystal_renderer import (
    # Constants
    AXIS_COLOURS,
    ELEMENT_COLOURS,
    FORM_COLORS,
    HABIT_COLOURS,
    blend_colors,
    calculate_axis_origin,
    calculate_bounding_box,
    calculate_vertex_visibility,
    # Projection
    calculate_view_direction,
    cell_to_vectors,
    export_gltf,
    # Format exports
    export_stl,
    format_property_value,
    geometry_to_gltf,
    geometry_to_stl,
    # Rendering helpers
    get_element_colour,
    # Info panel
    get_property_label,
)

# =============================================================================
# Constants Tests
# =============================================================================


class TestConstants:
    """Test data constants."""

    def test_axis_colours(self):
        """Test axis colours are defined."""
        assert "a" in AXIS_COLOURS
        assert "b" in AXIS_COLOURS
        assert "c" in AXIS_COLOURS
        assert all(c.startswith("#") for c in AXIS_COLOURS.values())

    def test_element_colours(self):
        """Test element colours are defined."""
        assert "C" in ELEMENT_COLOURS
        assert "O" in ELEMENT_COLOURS
        assert "Si" in ELEMENT_COLOURS

    def test_habit_colours(self):
        """Test habit colours for all crystal systems."""
        systems = [
            "cubic",
            "tetragonal",
            "hexagonal",
            "trigonal",
            "orthorhombic",
            "monoclinic",
            "triclinic",
        ]
        for system in systems:
            assert system in HABIT_COLOURS
            assert "face" in HABIT_COLOURS[system]
            assert "edge" in HABIT_COLOURS[system]

    def test_form_colors(self):
        """Test form colors list."""
        assert len(FORM_COLORS) >= 4
        for color in FORM_COLORS:
            assert "face" in color
            assert "edge" in color


# =============================================================================
# Projection Tests
# =============================================================================


class TestProjection:
    """Test projection utilities."""

    def test_calculate_view_direction(self):
        """Test view direction calculation."""
        # Looking straight at XY plane from above
        view_dir = calculate_view_direction(90, 0)
        assert np.allclose(view_dir, [0, 0, 1], atol=1e-10)

        # Looking from front
        view_dir = calculate_view_direction(0, 0)
        assert np.allclose(view_dir, [1, 0, 0], atol=1e-10)

    def test_calculate_axis_origin(self):
        """Test axis origin calculation."""
        # Simple cube vertices
        vertices = np.array(
            [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [1, 0, 1], [0, 1, 1], [1, 1, 1]]
        )
        origin, length = calculate_axis_origin(vertices)

        # Origin should be near the min corner
        assert origin[0] < 0
        assert origin[1] < 0
        assert origin[2] < 0

        # Length should be reasonable
        assert 0 < length < 1

    def test_calculate_vertex_visibility(self):
        """Test vertex visibility calculation."""
        # Octahedron vertices
        vertices = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]])
        faces = [
            [0, 2, 4],
            [0, 4, 3],
            [0, 3, 5],
            [0, 5, 2],
            [1, 4, 2],
            [1, 3, 4],
            [1, 5, 3],
            [1, 2, 5],
        ]

        visibility = calculate_vertex_visibility(vertices, faces, 30, -45)
        assert len(visibility) == 6
        assert visibility.dtype == bool

    def test_cell_to_vectors_cubic(self):
        """Test cell parameter to vector conversion for cubic."""
        cellpar = [1, 1, 1, 90, 90, 90]
        va, vb, vc = cell_to_vectors(cellpar)

        assert np.allclose(va, [1, 0, 0], atol=1e-10)
        assert np.allclose(vb, [0, 1, 0], atol=1e-10)
        assert np.allclose(vc, [0, 0, 1], atol=1e-10)

    def test_calculate_bounding_box(self):
        """Test bounding box calculation."""
        vertices = np.array([[-1, -2, -3], [4, 5, 6]])
        min_bounds, max_bounds = calculate_bounding_box(vertices)

        assert np.allclose(min_bounds, [-1, -2, -3])
        assert np.allclose(max_bounds, [4, 5, 6])


# =============================================================================
# Rendering Helper Tests
# =============================================================================


class TestRenderingHelpers:
    """Test rendering helper functions."""

    def test_get_element_colour_known(self):
        """Test colour for known element."""
        colour = get_element_colour("C")
        assert colour == "#909090"

    def test_get_element_colour_unknown(self):
        """Test colour for unknown element."""
        colour = get_element_colour("Xx")
        assert colour.startswith("#")

    def test_blend_colors(self):
        """Test color blending."""
        # Blend white and black
        blended = blend_colors("#ffffff", "#000000")
        # Should be middle grey
        assert blended.lower() in ["#7f7f7f", "#808080"]

        # Blend red and blue
        blended = blend_colors("#ff0000", "#0000ff")
        assert blended.lower() == "#7f007f"


# =============================================================================
# Info Panel Tests
# =============================================================================


class TestInfoPanel:
    """Test info panel functions."""

    def test_get_property_label_known(self):
        """Test label for known property."""
        assert get_property_label("hardness") == "Hardness"
        assert get_property_label("sg") == "S.G."
        assert get_property_label("ri") == "R.I."

    def test_get_property_label_unknown(self):
        """Test label for unknown property."""
        label = get_property_label("some_custom_property")
        assert label == "Some Custom Property"

    def test_format_property_value_string(self):
        """Test formatting string value."""
        assert format_property_value("name", "Ruby") == "Ruby"

    def test_format_property_value_none(self):
        """Test formatting None value."""
        assert format_property_value("unknown", None) == "-"

    def test_format_property_value_list(self):
        """Test formatting list value."""
        result = format_property_value("colors", ["red", "blue", "green"])
        assert "red" in result
        assert "blue" in result

    def test_format_property_value_float(self):
        """Test formatting float value."""
        result = format_property_value("ri", 1.544)
        assert "1.54" in result


# =============================================================================
# STL Export Tests
# =============================================================================


class TestSTLExport:
    """Test STL export functions."""

    @pytest.fixture
    def cube_geometry(self):
        """Create a simple cube geometry."""
        vertices = np.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [1, 1, 0],
                [0, 1, 0],
                [0, 0, 1],
                [1, 0, 1],
                [1, 1, 1],
                [0, 1, 1],
            ],
            dtype=np.float32,
        )
        faces = [
            [0, 3, 2, 1],  # Bottom
            [4, 5, 6, 7],  # Top
            [0, 1, 5, 4],  # Front
            [2, 3, 7, 6],  # Back
            [0, 4, 7, 3],  # Left
            [1, 2, 6, 5],  # Right
        ]
        return vertices, faces

    def test_geometry_to_stl_binary(self, cube_geometry):
        """Test binary STL generation."""
        vertices, faces = cube_geometry
        stl_data = geometry_to_stl(vertices, faces, binary=True)

        assert isinstance(stl_data, bytes)
        assert len(stl_data) > 84  # Header + count + at least 1 triangle

    def test_geometry_to_stl_ascii(self, cube_geometry):
        """Test ASCII STL generation."""
        vertices, faces = cube_geometry
        stl_data = geometry_to_stl(vertices, faces, binary=False)

        stl_text = stl_data.decode("ascii")
        assert stl_text.startswith("solid crystal")
        assert "endsolid crystal" in stl_text
        assert "facet normal" in stl_text

    def test_export_stl(self, cube_geometry):
        """Test STL file export."""
        vertices, faces = cube_geometry

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.stl"
            result = export_stl(vertices, faces, output_path)

            assert result.exists()
            assert result.stat().st_size > 0


# =============================================================================
# glTF Export Tests
# =============================================================================


class TestGLTFExport:
    """Test glTF export functions."""

    @pytest.fixture
    def cube_geometry(self):
        """Create a simple cube geometry."""
        vertices = np.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [1, 1, 0],
                [0, 1, 0],
                [0, 0, 1],
                [1, 0, 1],
                [1, 1, 1],
                [0, 1, 1],
            ],
            dtype=np.float32,
        )
        faces = [
            [0, 3, 2, 1],  # Bottom
            [4, 5, 6, 7],  # Top
            [0, 1, 5, 4],  # Front
            [2, 3, 7, 6],  # Back
            [0, 4, 7, 3],  # Left
            [1, 2, 6, 5],  # Right
        ]
        return vertices, faces

    def test_geometry_to_gltf(self, cube_geometry):
        """Test glTF JSON generation."""
        vertices, faces = cube_geometry
        gltf = geometry_to_gltf(vertices, faces)

        assert "asset" in gltf
        assert gltf["asset"]["version"] == "2.0"
        assert "meshes" in gltf
        assert "buffers" in gltf
        assert "accessors" in gltf

    def test_geometry_to_gltf_with_color(self, cube_geometry):
        """Test glTF with custom color."""
        vertices, faces = cube_geometry
        gltf = geometry_to_gltf(vertices, faces, color=(0.5, 0.7, 0.9, 0.8))

        assert "materials" in gltf
        material = gltf["materials"][0]
        assert "pbrMetallicRoughness" in material
        assert material["pbrMetallicRoughness"]["baseColorFactor"] == [0.5, 0.7, 0.9, 0.8]

    def test_export_gltf(self, cube_geometry):
        """Test glTF file export."""
        vertices, faces = cube_geometry

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.gltf"
            result = export_gltf(vertices, faces, output_path)

            assert result.exists()
            assert result.stat().st_size > 0

            # Verify it's valid JSON
            import json

            with open(result) as f:
                data = json.load(f)
            assert "asset" in data


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests with crystal-geometry."""

    def test_octahedron_to_stl(self):
        """Test exporting octahedron to STL."""
        try:
            from crystal_geometry import create_octahedron
        except ImportError:
            pytest.skip("crystal-geometry not installed")

        geom = create_octahedron()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "octahedron.stl"
            result = export_stl(geom.vertices, geom.faces, output_path)

            assert result.exists()
            assert result.stat().st_size > 0

    def test_cube_to_gltf(self):
        """Test exporting cube to glTF."""
        try:
            from crystal_geometry import create_cube
        except ImportError:
            pytest.skip("crystal-geometry not installed")

        geom = create_cube()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cube.gltf"
            result = export_gltf(geom.vertices, geom.faces, output_path, color=(0.5, 0.8, 1.0, 0.9))

            assert result.exists()
