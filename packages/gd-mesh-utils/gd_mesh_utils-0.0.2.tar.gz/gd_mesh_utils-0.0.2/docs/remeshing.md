# Remeshing

`gdmesh` wraps the [`pymmg`](https://pypi.org/project/pymmg/) executables to remesh surfaces (`mmgs`), volumes (`mmg3d`), and 2D meshes (`mmg2d`). Use **surface** remeshing for triangular surface meshes (e.g. STL), **volume** for tetrahedral meshes, and **2D** for planar triangle meshes in the xy-plane.

## Surface remeshing

```python
from gdmesh.remesh import MmgOptions
import gdmesh as gm

mesh = gm.Mesh.load("surface.vtk")
opts = MmgOptions(hmax=0.3, hmin=0.05, hausd=0.01, hgrad=1.3)
remeshed = mesh.remesh_surface(mmg_args=opts)
```

## Volume remeshing

```python
from gdmesh.remesh import MmgOptions
import gdmesh as gm

mesh = gm.Mesh.load("volume.vtk")
opts = MmgOptions(hmax=0.4, hmin=0.1, hausd=0.02, hgrad=1.2)
remeshed = mesh.remesh_volume(mmg_args=opts)
```

## Notes

- Pass `mmg_args=None` for defaults or a list of CLI-style arguments.
- `MmgOptions` is a convenience helper to build argument lists.
