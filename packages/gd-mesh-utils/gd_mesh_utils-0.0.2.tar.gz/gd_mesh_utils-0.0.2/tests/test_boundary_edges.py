import numpy as np
import pyvista as pv

import gdmesh as gm


def _triangles_from_pv(poly: pv.PolyData) -> np.ndarray:
    triangulated = poly.triangulate()
    faces = triangulated.faces.reshape(-1, 4)
    if not np.all(faces[:, 0] == 3):
        raise ValueError("Expected triangle faces after triangulation.")
    return faces[:, 1:4]


def test_boundary_edges_on_disc():
    disc = pv.Disc(inner=0.25, outer=1.0, r_res=8, c_res=32).triangulate()
    triangles = _triangles_from_pv(disc)
    mesh = gm.Mesh(points=disc.points, cells={"triangle": triangles})

    loops = mesh.boundary_edges()
    assert len(loops) == 2

    max_idx = mesh.points.shape[0] - 1
    for loop in loops:
        assert len(loop) > 0
        for edge in loop:
            assert len(edge) == 2
            assert 0 <= edge[0] <= max_idx
            assert 0 <= edge[1] <= max_idx
        for i in range(len(loop) - 1):
            assert loop[i][1] == loop[i + 1][0]
        assert loop[-1][1] == loop[0][0]


def test_boundary_edges_single_loop():
    """Open surface with one boundary loop (e.g. a plane = rectangle)."""
    plane = pv.Plane(i_resolution=2, j_resolution=2).triangulate()
    triangles = _triangles_from_pv(plane)
    mesh = gm.Mesh(points=plane.points, cells={"triangle": triangles})

    loops = mesh.boundary_edges()
    assert len(loops) == 1
    loop = loops[0]
    assert len(loop) > 0
    max_idx = mesh.points.shape[0] - 1
    for edge in loop:
        assert len(edge) == 2
        assert 0 <= edge[0] <= max_idx
        assert 0 <= edge[1] <= max_idx
    for i in range(len(loop) - 1):
        assert loop[i][1] == loop[i + 1][0]
    assert loop[-1][1] == loop[0][0]
