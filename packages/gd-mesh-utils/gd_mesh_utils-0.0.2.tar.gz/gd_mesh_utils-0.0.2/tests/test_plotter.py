import numpy as np
import pyvista as pv

import gdmesh as gm


def _simple_triangle_mesh() -> gm.Mesh:
    points = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.5, 1.0, 0.0],
        ]
    )
    cells = {"triangle": np.array([[0, 1, 2]])}
    return gm.Mesh(points=points, cells=cells)


def test_plotter_add_mesh_accepts_gdmesh_mesh(monkeypatch):
    captured = {}

    def fake_add_mesh(self, mesh, *args, **kwargs):
        captured["mesh"] = mesh
        return "ok"

    monkeypatch.setattr(pv.Plotter, "add_mesh", fake_add_mesh)
    mesh = _simple_triangle_mesh()
    plotter = gm.Plotter(off_screen=True)

    result = plotter.add_mesh(mesh)

    assert result == "ok"
    assert captured["mesh"] is mesh.pv_mesh
    plotter.close()


def test_plotter_save_calls_screenshot(monkeypatch):
    captured = {}

    def fake_screenshot(self, fname, *args, **kwargs):
        captured["fname"] = fname
        return "sentinel"

    monkeypatch.setattr(pv.Plotter, "screenshot", fake_screenshot)
    plotter = gm.Plotter(off_screen=True)

    result = plotter.save("plot.png")

    assert result == "sentinel"
    assert captured["fname"] == "plot.png"
    plotter.close()


def test_plotter_getitem_returns_self(monkeypatch):
    captured = {}

    def fake_subplot(self, row, col):
        captured["pos"] = (row, col)

    monkeypatch.setattr(pv.Plotter, "subplot", fake_subplot)
    plotter = gm.Plotter(off_screen=True)

    returned = plotter[(0, 0)]

    assert returned is plotter
    assert captured["pos"] == (0, 0)
    plotter.close()
