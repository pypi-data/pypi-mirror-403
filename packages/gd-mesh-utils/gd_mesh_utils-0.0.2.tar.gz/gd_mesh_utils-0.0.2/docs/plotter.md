# Plotter

`Plotter` is a convenience wrapper around `pyvista.Plotter` that accepts
`gdmesh.Mesh` instances directly.

## Highlights

- Defaults to a `DocumentTheme` with a white background and visible edges.
- Context manager adds a camera orientation widget and calls `show()` on exit.
- `save(path)` delegates to `screenshot(path)`.

## Basic usage

```python
import gdmesh as gm

mesh = gm.Mesh.load("input.vtk")
with gm.Plotter(off_screen=True) as pl:
    pl.add_mesh(mesh)
    pl.save("preview.png")
```

## Notes

`Plotter.add_mesh` accepts either a `gdmesh.Mesh` or a pyvista dataset.
