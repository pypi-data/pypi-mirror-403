"""Tests for Wavefront OBJ export."""

import numpy as np

from crystal_renderer.formats.obj import (
    export_obj,
    geometry_to_obj,
    geometry_to_obj_with_groups,
)


class TestGeometryToObj:
    """Tests for geometry_to_obj function."""

    def test_basic_triangle(self):
        """Should export a basic triangle."""
        vertices = np.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [0, 1, 0],
            ],
            dtype=np.float64,
        )
        faces = [[0, 1, 2]]

        obj_content, mtl_content = geometry_to_obj(
            vertices, faces, name="triangle", include_mtl=False
        )

        # Check vertices
        assert "v 0.000000 0.000000 0.000000" in obj_content
        assert "v 1.000000 0.000000 0.000000" in obj_content
        assert "v 0.000000 1.000000 0.000000" in obj_content

        # Check face (1-indexed)
        assert "f 1 2 3" in obj_content

        # No MTL when disabled
        assert mtl_content is None

    def test_with_material(self):
        """Should generate material file when requested."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float64)
        faces = [[0, 1, 2]]

        obj_content, mtl_content = geometry_to_obj(vertices, faces, name="test", include_mtl=True)

        # Should reference material file
        assert "mtllib test.mtl" in obj_content
        assert "usemtl crystal_material" in obj_content

        # Material file should have content
        assert mtl_content is not None
        assert "newmtl crystal_material" in mtl_content
        assert "Kd" in mtl_content

    def test_with_normals(self):
        """Should include face normals when provided."""
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

        obj_content, _ = geometry_to_obj(vertices, faces, face_normals=normals, include_mtl=False)

        # Should have vertex normal
        assert "vn 0.000000 0.000000 1.000000" in obj_content

        # Face should reference normal
        assert "//" in obj_content  # v//vn format

    def test_cube_faces(self):
        """Should correctly export cube with quad faces."""
        # Simple cube centered at origin
        s = 1.0
        vertices = np.array(
            [
                [-s, -s, -s],
                [s, -s, -s],
                [s, s, -s],
                [-s, s, -s],
                [-s, -s, s],
                [s, -s, s],
                [s, s, s],
                [-s, s, s],
            ],
            dtype=np.float64,
        )

        faces = [
            [0, 1, 2, 3],  # Bottom
            [4, 5, 6, 7],  # Top
            [0, 1, 5, 4],  # Front
            [2, 3, 7, 6],  # Back
            [0, 4, 7, 3],  # Left
            [1, 2, 6, 5],  # Right
        ]

        obj_content, _ = geometry_to_obj(vertices, faces, include_mtl=False)

        # Should have 8 vertices
        assert obj_content.count("\nv ") == 8

        # Should have 6 faces
        assert obj_content.count("\nf ") == 6


class TestGeometryToObjWithGroups:
    """Tests for multi-material OBJ export."""

    def test_with_face_groups(self):
        """Should separate faces by group."""
        vertices = np.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [0, 1, 0],
                [2, 0, 0],
                [3, 0, 0],
                [2, 1, 0],
            ],
            dtype=np.float64,
        )

        faces = [[0, 1, 2], [3, 4, 5]]
        face_groups = [0, 1]

        obj_content, mtl_content = geometry_to_obj_with_groups(
            vertices, faces, face_groups=face_groups
        )

        # Should have group definitions
        assert "g " in obj_content

        # Should have multiple materials
        assert "usemtl material_0" in obj_content
        assert "usemtl material_1" in obj_content

        # MTL should have both materials
        assert "newmtl material_0" in mtl_content
        assert "newmtl material_1" in mtl_content

    def test_default_groups(self):
        """Should default to all faces in group 0."""
        vertices = np.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [0, 1, 0],
            ],
            dtype=np.float64,
        )
        faces = [[0, 1, 2]]

        obj_content, _ = geometry_to_obj_with_groups(vertices, faces)

        # Should have single group
        assert obj_content.count("usemtl material_") == 1


class TestExportObj:
    """Tests for file export function."""

    def test_export_creates_file(self, tmp_path):
        """Should create OBJ file."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float64)
        faces = [[0, 1, 2]]

        filepath = tmp_path / "test.obj"
        export_obj(vertices, faces, str(filepath), include_mtl=False)

        assert filepath.exists()

        content = filepath.read_text()
        assert "v " in content
        assert "f " in content

    def test_export_creates_mtl_file(self, tmp_path):
        """Should create companion MTL file."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float64)
        faces = [[0, 1, 2]]

        filepath = tmp_path / "test.obj"
        export_obj(vertices, faces, str(filepath), include_mtl=True)

        mtl_path = tmp_path / "test.mtl"
        assert filepath.exists()
        assert mtl_path.exists()

    def test_export_uses_filename_as_name(self, tmp_path):
        """Should derive name from filename."""
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float64)
        faces = [[0, 1, 2]]

        filepath = tmp_path / "my_crystal.obj"
        export_obj(vertices, faces, str(filepath), include_mtl=True)

        content = filepath.read_text()
        assert "my_crystal.mtl" in content
