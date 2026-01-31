import tempfile
from pathlib import Path

import numpy as np
import pyvista as pv

import gdmesh as gm


def _triangles_from_pv(poly: pv.PolyData) -> np.ndarray:
    triangulated = poly.triangulate()
    faces = triangulated.faces.reshape(-1, 4)
    if not np.all(faces[:, 0] == 3):
        raise ValueError("Expected triangle faces after triangulation.")
    return faces[:, 1:4]


def test_mesh_from_sphere():
    sphere = pv.Sphere(theta_resolution=8, phi_resolution=8)
    triangles = _triangles_from_pv(sphere)
    mesh = gm.Mesh(points=sphere.points, cells={"triangle": triangles})

    assert mesh.points.shape[1] == 3
    assert "triangle" in mesh.cells
    assert mesh.cells["triangle"].shape[1] == 3
    assert mesh.point_data == {}
    assert mesh.cell_data == {}
    assert mesh.pv_mesh.n_points == sphere.n_points
    assert mesh.pv_mesh.n_cells == triangles.shape[0]


def test_mesh_from_cube_with_data():
    cube = pv.Cube().triangulate()
    triangles = _triangles_from_pv(cube)
    point_data = {"id": np.arange(cube.n_points)}
    cell_data = {"cell_id": np.arange(triangles.shape[0])}
    mesh = gm.Mesh(
        points=cube.points,
        cells={"triangle": triangles},
        point_data=point_data,
        cell_data=cell_data,
    )

    assert mesh.points.shape == cube.points.shape
    assert mesh.cells["triangle"].shape == triangles.shape
    assert np.array_equal(mesh.point_data["id"], point_data["id"])
    assert np.array_equal(mesh.cell_data["cell_id"], cell_data["cell_id"])
    assert mesh.pv_mesh.n_cells == triangles.shape[0]


def test_mesh_load_save_round_trip():
    """Round-trip: save mesh to temp file, load back, compare points and cells."""
    cube = pv.Cube().triangulate()
    triangles = _triangles_from_pv(cube)
    point_data = {"id": np.arange(cube.n_points, dtype=float)}
    cell_data = {"cell_id": np.arange(triangles.shape[0], dtype=float)}
    mesh = gm.Mesh(
        points=cube.points,
        cells={"triangle": triangles},
        point_data=point_data,
        cell_data=cell_data,
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "mesh.vtk"
        mesh.save(path)
        loaded = gm.Mesh.load(path)
    assert loaded.points.shape == mesh.points.shape
    assert np.allclose(loaded.points, mesh.points)
    assert set(loaded.cells.keys()) == set(mesh.cells.keys())
    for key in mesh.cells:
        assert np.array_equal(loaded.cells[key], mesh.cells[key])
    assert set(loaded.point_data.keys()) == set(mesh.point_data.keys())
    for key in mesh.point_data:
        assert np.allclose(loaded.point_data[key], mesh.point_data[key])
    assert set(loaded.cell_data.keys()) == set(mesh.cell_data.keys())
    for key in mesh.cell_data:
        assert np.allclose(loaded.cell_data[key], mesh.cell_data[key])


def _cube_mesh() -> gm.Mesh:
    cube = pv.Cube().triangulate()
    triangles = _triangles_from_pv(cube)
    return gm.Mesh(points=cube.points, cells={"triangle": triangles})


def test_intersect_line_through_cube():
    mesh = _cube_mesh()
    intersections = mesh.intersect([-1.0, 0.0, 0.0], [1.0, 0.0, 0.0])

    assert intersections.shape == (2, 3)
    xs = np.sort(intersections[:, 0])
    assert np.allclose(xs, [-0.5, 0.5], atol=1e-6)
    assert np.allclose(intersections[:, 1:], 0.0, atol=1e-6)


def test_build_locators_and_closest_queries():
    mesh = _cube_mesh()

    mesh.buildPointLocator()
    mesh.buildCellLocator()
    assert mesh.pointLocator is not None
    assert mesh.cellLocator is not None

    query_point = np.array([2.0, 0.25, -0.25])
    closest_point = mesh.closestPoint(query_point)
    assert isinstance(closest_point, gm.PairIdCoord)
    assert closest_point.coord.shape == (3,)

    distances = np.linalg.norm(mesh.points - query_point, axis=1)
    expected_idx = int(np.argmin(distances))
    assert closest_point.idx == expected_idx
    assert np.allclose(closest_point.coord, mesh.points[expected_idx])

    closest_cell = mesh.closestCell([2.0, 0.0, 0.0])
    assert isinstance(closest_cell, gm.PairIdCoord)
    assert closest_cell.coord.shape == (3,)
    assert np.allclose(closest_cell.coord, [0.5, 0.0, 0.0], atol=1e-6)