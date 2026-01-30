"""
Tests for crystal visualization functions.

Tests for generate_cdl_svg, generate_geometry_svg, and related
high-level visualization functions.
"""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from crystal_renderer.visualization import (
    generate_cdl_svg,
    generate_geometry_svg,
)


class TestGenerateCDLSVG:
    """Tests for generate_cdl_svg function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_basic_octahedron(self, temp_dir):
        """Generate SVG for a basic octahedron."""
        output_path = temp_dir / "octahedron.svg"
        result = generate_cdl_svg("cubic[m3m]:{111}@1.0", output_path)

        assert result.exists()
        assert result.stat().st_size > 0

        # Check it's valid SVG
        content = result.read_text()
        assert "<svg" in content
        assert "</svg>" in content

    def test_truncated_octahedron(self, temp_dir):
        """Generate SVG for truncated octahedron (multiple forms)."""
        output_path = temp_dir / "truncated.svg"
        result = generate_cdl_svg("cubic[m3m]:{111}@1.0 + {100}@1.3", output_path)

        assert result.exists()
        content = result.read_text()
        assert "<svg" in content

    def test_with_axes(self, temp_dir):
        """Generate SVG with crystallographic axes."""
        output_path = temp_dir / "with_axes.svg"
        result = generate_cdl_svg("cubic[m3m]:{111}@1.0", output_path, show_axes=True)

        assert result.exists()

    def test_without_axes(self, temp_dir):
        """Generate SVG without crystallographic axes."""
        output_path = temp_dir / "no_axes.svg"
        result = generate_cdl_svg("cubic[m3m]:{111}@1.0", output_path, show_axes=False)

        assert result.exists()

    def test_color_by_form(self, temp_dir):
        """Generate SVG with faces colored by form."""
        output_path = temp_dir / "color_by_form.svg"
        result = generate_cdl_svg(
            "cubic[m3m]:{111}@1.0 + {100}@1.3", output_path, color_by_form=True
        )

        assert result.exists()

    def test_custom_view_angles(self, temp_dir):
        """Generate SVG with custom view angles."""
        output_path = temp_dir / "custom_view.svg"
        result = generate_cdl_svg("cubic[m3m]:{111}@1.0", output_path, elev=45, azim=-30)

        assert result.exists()

    def test_without_grid(self, temp_dir):
        """Generate SVG without background grid."""
        output_path = temp_dir / "no_grid.svg"
        result = generate_cdl_svg("cubic[m3m]:{111}@1.0", output_path, show_grid=False)

        assert result.exists()

    def test_hexagonal_system(self, temp_dir):
        """Generate SVG for hexagonal crystal system."""
        output_path = temp_dir / "hexagonal.svg"
        result = generate_cdl_svg("hexagonal[6/mmm]:{10-10}@1.0 + {0001}@0.5", output_path)

        assert result.exists()
        content = result.read_text()
        assert "<svg" in content

    def test_trigonal_system(self, temp_dir):
        """Generate SVG for trigonal crystal system."""
        output_path = temp_dir / "trigonal.svg"
        result = generate_cdl_svg("trigonal[-3m]:{10-11}@1.0", output_path)

        assert result.exists()

    def test_with_info_properties(self, temp_dir):
        """Generate SVG with info panel."""
        output_path = temp_dir / "with_info.svg"
        result = generate_cdl_svg(
            "cubic[m3m]:{111}@1.0",
            output_path,
            info_properties={"name": "Diamond", "hardness": 10, "chemistry": "C"},
        )

        assert result.exists()

    def test_custom_figsize(self, temp_dir):
        """Generate SVG with custom figure size."""
        output_path = temp_dir / "custom_size.svg"
        result = generate_cdl_svg("cubic[m3m]:{111}@1.0", output_path, figsize=(8, 8))

        assert result.exists()


class TestGenerateGeometrySVG:
    """Tests for generate_geometry_svg function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def cube_geometry(self):
        """Create cube vertices and faces."""
        vertices = np.array(
            [
                [-1, -1, -1],
                [1, -1, -1],
                [1, 1, -1],
                [-1, 1, -1],
                [-1, -1, 1],
                [1, -1, 1],
                [1, 1, 1],
                [-1, 1, 1],
            ],
            dtype=np.float64,
        )
        faces = [
            [0, 1, 2, 3],  # Bottom
            [4, 7, 6, 5],  # Top
            [0, 4, 5, 1],  # Front
            [2, 6, 7, 3],  # Back
            [0, 3, 7, 4],  # Left
            [1, 5, 6, 2],  # Right
        ]
        return vertices, faces

    @pytest.fixture
    def octahedron_geometry(self):
        """Create octahedron vertices and faces."""
        vertices = np.array(
            [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]], dtype=np.float64
        )
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
        return vertices, faces

    def test_basic_cube(self, temp_dir, cube_geometry):
        """Generate SVG for a basic cube."""
        vertices, faces = cube_geometry
        output_path = temp_dir / "cube.svg"

        result = generate_geometry_svg(vertices, faces, output_path)

        assert result.exists()
        content = result.read_text()
        assert "<svg" in content
        assert "</svg>" in content

    def test_octahedron(self, temp_dir, octahedron_geometry):
        """Generate SVG for an octahedron."""
        vertices, faces = octahedron_geometry
        output_path = temp_dir / "octahedron.svg"

        result = generate_geometry_svg(vertices, faces, output_path)

        assert result.exists()

    def test_with_title(self, temp_dir, cube_geometry):
        """Generate SVG with custom title."""
        vertices, faces = cube_geometry
        output_path = temp_dir / "titled.svg"

        result = generate_geometry_svg(vertices, faces, output_path, title="Test Crystal")

        assert result.exists()

    def test_custom_colors(self, temp_dir, cube_geometry):
        """Generate SVG with custom face/edge colors."""
        vertices, faces = cube_geometry
        output_path = temp_dir / "colored.svg"

        result = generate_geometry_svg(
            vertices, faces, output_path, face_color="#FF6B6B", edge_color="#C92A2A"
        )

        assert result.exists()

    def test_without_axes(self, temp_dir, cube_geometry):
        """Generate SVG without axes."""
        vertices, faces = cube_geometry
        output_path = temp_dir / "no_axes.svg"

        result = generate_geometry_svg(vertices, faces, output_path, show_axes=False)

        assert result.exists()

    def test_without_grid(self, temp_dir, cube_geometry):
        """Generate SVG without grid."""
        vertices, faces = cube_geometry
        output_path = temp_dir / "no_grid.svg"

        result = generate_geometry_svg(vertices, faces, output_path, show_grid=False)

        assert result.exists()

    def test_custom_view(self, temp_dir, cube_geometry):
        """Generate SVG with custom view angles."""
        vertices, faces = cube_geometry
        output_path = temp_dir / "custom_view.svg"

        result = generate_geometry_svg(vertices, faces, output_path, elev=60, azim=-60)

        assert result.exists()

    def test_with_info_properties(self, temp_dir, cube_geometry):
        """Generate SVG with info panel."""
        vertices, faces = cube_geometry
        output_path = temp_dir / "with_info.svg"

        result = generate_geometry_svg(
            vertices,
            faces,
            output_path,
            info_properties={"vertices": len(cube_geometry[0]), "faces": len(cube_geometry[1])},
        )

        assert result.exists()


class TestVisualizationIntegration:
    """Integration tests with crystal-geometry package."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_diamond_crystal(self, temp_dir):
        """Generate diamond-like truncated octahedron."""
        output_path = temp_dir / "diamond.svg"
        result = generate_cdl_svg(
            "cubic[m3m]:{111}@1.0 + {100}@1.4", output_path, color_by_form=True, show_axes=True
        )

        assert result.exists()
        content = result.read_text()
        assert "<svg" in content
        # Check title includes forms
        assert "Cubic" in content

    def test_quartz_prism(self, temp_dir):
        """Generate quartz prism with rhombohedron."""
        output_path = temp_dir / "quartz.svg"
        result = generate_cdl_svg(
            "trigonal[32]:{10-10}@1.0 + {10-11}@0.8", output_path, show_axes=True
        )

        assert result.exists()

    def test_beryl_crystal(self, temp_dir):
        """Generate beryl hexagonal prism with pinacoid."""
        output_path = temp_dir / "beryl.svg"
        result = generate_cdl_svg(
            "hexagonal[6/mmm]:{10-10}@1.0 + {0001}@0.6", output_path, color_by_form=True
        )

        assert result.exists()
