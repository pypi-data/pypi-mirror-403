# [gdmesh](https://gdmesh-a2ef81.gitlabpages.inria.fr)

**gdmesh** is a lightweight mesh utility layer that wraps `pyvista` meshes with
simple numpy access, format-agnostic I/O via `meshio`, and remeshing through
`pymmg` (mmgs/mmg3d).

## Installation

```bash
pip install gd-mesh-utils
```

## What it does

- Wraps mesh points/cells in a small `Mesh` class with numpy accessors.
- Reads and writes many mesh formats through `meshio`.
- Remeshes surfaces or volumes using `pymmg` executables.
- Exposes the underlying `pyvista` dataset for advanced operations.

## Key API

### `Mesh`

- `Mesh(points, cells, point_data=None, cell_data=None)` constructs a mesh.
- `Mesh.load(path)` loads from disk using `meshio`.
- `mesh.save(path)` saves to disk using `meshio`.

### Convenience helpers

- `gdmesh.load_mesh(path)` is a shortcut for `Mesh.load(path)`.
- `gdmesh.remesh.MmgOptions(hmax, hmin, hausd, hgrad)` builds mmg args.
- `gdmesh.get_boundary_edges(mesh, mesh_for_ids=None, rev=True)` extracts boundary edge
  loops from open surfaces.

### VTK spatial ops

`Mesh` includes VTK-powered spatial queries via `VtkMeshOpsMixin`:

- `mesh.intersect(p0, p1)` returns intersection points with a line segment.
- `mesh.closestPoint(point)` returns the nearest point id + coordinates.
- `mesh.closestCell(point)` returns the nearest cell id + coordinates.

## Mesh data model

- `mesh.points` is a numpy array of shape `(n_points, 3)`.
- `mesh.cells` is a dict of cell arrays keyed by type (e.g. `"triangle"`).
- `mesh.point_data` and `mesh.cell_data` are dicts of numpy arrays.

Supported cell types: `vertex`, `point`, `line`, `triangle`, `quad`, `tetra`.

## Examples

### Load, inspect, save

```python
import gdmesh as gm

mesh = gm.Mesh.load("input.vtk")
print(mesh.points.shape)
print(mesh.cells.keys())
mesh.save("output.obj")
```

### Build a mesh from arrays

```python
import numpy as np
import gdmesh as gm

points = np.array(
    [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.5, 1.0, 0.0],
    ]
)
cells = {"triangle": np.array([[0, 1, 2]])}
mesh = gm.Mesh(points=points, cells=cells)
```

For advanced topics, see:

- Plotting in `plotter.md`
- Boundary extraction in `boundary-edges.md`
- VTK spatial queries in `vtk-ops.md`
- Remeshing in `remeshing.md`
