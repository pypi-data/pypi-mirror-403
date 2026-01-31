import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pyvista as pv

import gdmesh as gm


def _triangles_from_pv(poly: pv.PolyData) -> np.ndarray:
    triangulated = poly.triangulate()
    faces = triangulated.faces.reshape(-1, 4)
    if not np.all(faces[:, 0] == 3):
        raise ValueError("Expected triangle faces after triangulation.")
    return faces[:, 1:4]


def test_remesh_surface_calls_mmgs_with_expected_args():
    """With subprocess mocked, remesh_surface builds the expected mmgs command."""
    surface = pv.Cube().triangulate()
    triangles = _triangles_from_pv(surface)
    mesh = gm.Mesh(points=surface.points, cells={"triangle": triangles})
    fake_loaded = gm.Mesh(points=mesh.points.copy(), cells=mesh.cells)
    with patch("gdmesh.remesh.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = ("", "")
        mock_popen.return_value = mock_proc
        with patch.object(mesh.__class__, "load", return_value=fake_loaded):
            result = mesh.remesh_surface()
    assert result is fake_loaded
    mock_popen.assert_called_once()
    call_args = mock_popen.call_args[0][0]
    assert call_args[0] == sys.executable
    assert call_args[1] == "-m"
    assert call_args[2] == "mmgs"
    assert str(call_args[3]).endswith("input.mesh")
    assert str(call_args[4]).endswith("output.mesh")


def test_remesh_volume_tetra():
    points = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    cells = {"tetra": np.array([[0, 1, 2, 3]])}
    mesh = gm.Mesh(points=points, cells=cells)

    remeshed = mesh.remesh_volume()
    assert remeshed is not mesh
    assert remeshed.points.shape[1] == 3
    assert remeshed.cells
    assert all(block.size > 0 for block in remeshed.cells.values())


def test_remesh_surface_triangle():
    surface = pv.Cube().triangulate()
    triangles = _triangles_from_pv(surface)
    mesh = gm.Mesh(points=surface.points, cells={"triangle": triangles})

    remeshed = mesh.remesh_surface()
    assert remeshed is not mesh
    assert remeshed.points.shape[1] == 3
    assert remeshed.cells
    assert all(block.size > 0 for block in remeshed.cells.values())


def test_remesh_2d_triangle():
    plane = pv.Plane(i_resolution=4, j_resolution=4).triangulate()
    triangles = _triangles_from_pv(plane)
    mesh = gm.Mesh(points=plane.points, cells={"triangle": triangles})

    remeshed = mesh.remesh_2d()
    assert remeshed is not mesh
    assert remeshed.points.shape[1] == 3
    assert remeshed.cells
    assert all(block.size > 0 for block in remeshed.cells.values())
