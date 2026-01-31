"""gdmesh - Mesh utility library wrapping pyvista with meshio I/O and pymmg remeshing."""

from pathlib import Path
from typing import Union

from gdmesh.mesh import Mesh
from gdmesh.boundary_edges import get_boundary_edges, getBoundaryEdges
from gdmesh.remesh import MmgOptions
from gdmesh.plotter import Plotter
from gdmesh.vtk_ops import PairIdCoord, Points

__all__ = [
    "Mesh",
    "load_mesh",
    "MmgOptions",
    "Plotter",
    "PairIdCoord",
    "Points",
    "get_boundary_edges",
    "getBoundaryEdges",
]


def load_mesh(path: Union[str, Path]) -> Mesh:
    """Load mesh from file.

    Convenience function for Mesh.load().

    Args:
        path: Path to mesh file

    Returns:
        Mesh instance
    """
    return Mesh.load(path)
