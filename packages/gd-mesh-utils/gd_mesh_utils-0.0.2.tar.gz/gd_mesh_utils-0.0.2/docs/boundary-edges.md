# Boundary edges

Use `get_boundary_edges` to extract open boundary loops from a surface mesh. The
result is a list of ordered edge index pairs, one list per hole.

## Basic usage

```python
import gdmesh as gm

mesh = gm.Mesh.load("surface.vtk")
loops = gm.get_boundary_edges(mesh)
print(len(loops), "holes")
```

## Parameters

- `mesh_for_ids` (optional): mesh used to resolve point ids for the returned
  edges. Defaults to the same mesh.
- `rev` (bool): reverse the ordering of the returned loop.
