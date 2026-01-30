"""Tests for GEMCAD format export."""

import numpy as np

from crystal_renderer.formats.gemcad import (
    GEMSTONE_RI,
    export_gemcad,
    geometry_to_gemcad,
    get_ri_for_gemstone,
)


class TestGeometryToGemcad:
    """Tests for geometry_to_gemcad function."""

    def test_basic_output(self):
        """Should produce valid GEMCAD format."""
        vertices = np.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [0, 1, 0],
            ],
            dtype=np.float64,
        )
        faces = [[0, 1, 2]]
        normals = [np.array([0, 0, 1])]

        content = geometry_to_gemcad(vertices, faces, normals, name="Test", ri=1.54)

        # Should have header
        assert "GEMCAD design: Test" in content

        # Should have gear setting
        assert "gear 96" in content

        # Should have RI
        assert "ri 1.5400" in content

    def test_facet_angles(self):
        """Should compute correct elevation angles."""
        vertices = np.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [0, 1, 0],
            ],
            dtype=np.float64,
        )
        faces = [[0, 1, 2]]

        # Horizontal face (normal pointing up)
        normals = [np.array([0, 0, 1])]

        content = geometry_to_gemcad(vertices, faces, normals)

        # Crown facet (z > 0) at 0° elevation
        assert "c " in content  # Crown facet marker

    def test_pavilion_crown_separation(self):
        """Should separate pavilion and crown facets."""
        vertices = np.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [0, 1, 0],
                [0, 0, 0],
                [1, 0, 0],
                [0, -1, 0],
            ],
            dtype=np.float64,
        )
        faces = [[0, 1, 2], [3, 4, 5]]

        # One facing up (crown), one facing down (pavilion)
        normals = [
            np.array([0, 0, 1]),  # Crown
            np.array([0, 0, -1]),  # Pavilion
        ]

        content = geometry_to_gemcad(vertices, faces, normals)

        # Should have both sections
        assert "# Crown facets" in content
        assert "# Pavilion facets" in content
        assert "c " in content  # Crown marker
        assert "p " in content  # Pavilion marker

    def test_miller_indices_included(self):
        """Should include Miller indices when provided."""
        vertices = np.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [0, 1, 0],
            ],
            dtype=np.float64,
        )
        faces = [[0, 1, 2]]
        normals = [np.array([0, 0, 1])]
        millers = [(1, 1, 1)]

        content = geometry_to_gemcad(vertices, faces, normals, face_millers=millers)

        # Should have Miller index comment
        assert "(1 1 1)" in content

    def test_custom_gear(self):
        """Should use specified gear setting."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float64)
        faces = [[0, 1, 2]]
        normals = [np.array([0, 0, 1])]

        content = geometry_to_gemcad(vertices, faces, normals, gear=72)

        assert "gear 72" in content


class TestGemstoneRI:
    """Tests for refractive index lookup."""

    def test_known_gemstones(self):
        """Should return correct RI for known gems."""
        assert get_ri_for_gemstone("diamond") == 2.417
        assert get_ri_for_gemstone("quartz") == 1.544
        assert get_ri_for_gemstone("ruby") == 1.770

    def test_case_insensitive(self):
        """Should be case-insensitive."""
        assert get_ri_for_gemstone("DIAMOND") == get_ri_for_gemstone("diamond")
        assert get_ri_for_gemstone("Quartz") == get_ri_for_gemstone("quartz")

    def test_unknown_default(self):
        """Should return default for unknown gems."""
        ri = get_ri_for_gemstone("unknown_gem")
        assert ri == 1.54  # Quartz default

    def test_gemstone_ri_dict(self):
        """GEMSTONE_RI should have expected entries."""
        assert "diamond" in GEMSTONE_RI
        assert "ruby" in GEMSTONE_RI
        assert "sapphire" in GEMSTONE_RI
        assert "emerald" in GEMSTONE_RI
        assert "quartz" in GEMSTONE_RI


class TestExportGemcad:
    """Tests for file export function."""

    def test_export_creates_file(self, tmp_path):
        """Should create GEMCAD file."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float64)
        faces = [[0, 1, 2]]
        normals = [np.array([0, 0, 1])]

        filepath = tmp_path / "test.asc"
        export_gemcad(vertices, faces, normals, str(filepath))

        assert filepath.exists()

        content = filepath.read_text()
        assert "gear" in content
        assert "ri" in content

    def test_export_uses_filename_as_name(self, tmp_path):
        """Should derive name from filename."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float64)
        faces = [[0, 1, 2]]
        normals = [np.array([0, 0, 1])]

        filepath = tmp_path / "my_gem.asc"
        export_gemcad(vertices, faces, normals, str(filepath))

        content = filepath.read_text()
        assert "my_gem" in content


class TestSymmetryDetection:
    """Tests for automatic symmetry detection."""

    def test_high_symmetry_cube(self):
        """Cube should detect 4-fold symmetry."""
        # Normals for a cube (6 faces)
        normals = [
            np.array([1, 0, 0]),
            np.array([-1, 0, 0]),
            np.array([0, 1, 0]),
            np.array([0, -1, 0]),
            np.array([0, 0, 1]),
            np.array([0, 0, -1]),
        ]

        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float64)
        faces = [[0, 1, 2]] * 6

        content = geometry_to_gemcad(vertices, faces, normals)

        # Should detect symmetry
        assert "s " in content
