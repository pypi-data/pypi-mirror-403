# VTK operations

`Mesh` includes VTK-backed spatial queries from `VtkMeshOpsMixin`. These are
useful for proximity and intersection checks.

## Line intersection

```python
import gdmesh as gm

mesh = gm.Mesh.load("surface.vtk")
hits = mesh.intersect([0, 0, 0], [1, 0, 0])
```

## Closest point and cell

```python
import gdmesh as gm

mesh = gm.Mesh.load("surface.vtk")
closest_point = mesh.closestPoint([0.2, 0.1, 0.0])
closest_cell = mesh.closestCell([0.2, 0.1, 0.0])
print(closest_point.idx, closest_point.coord)
```

Both `closestPoint` and `closestCell` return a `PairIdCoord` with `idx` and
`coord` attributes.
