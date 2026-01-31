"""Mesh wrapper around pyvista with meshio I/O."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple, Union, TYPE_CHECKING

import numpy as np
import pyvista as pv
import meshio

from gdmesh.vtk_ops import VtkMeshOpsMixin

if TYPE_CHECKING:
    from gdmesh.remesh import MmgOptions

CellArray = np.ndarray
CellDict = Mapping[str, CellArray]
PointData = Mapping[str, np.ndarray]
CellDataInput = Mapping[str, Union[np.ndarray, Sequence[np.ndarray]]]


_CELL_TYPE_MAP: Dict[str, pv.CellType] = {
    "vertex": pv.CellType.VERTEX,
    "point": pv.CellType.VERTEX,
    "line": pv.CellType.LINE,
    "triangle": pv.CellType.TRIANGLE,
    "quad": pv.CellType.QUAD,
    "tetra": pv.CellType.TETRA,
}


def _as_2d_int_array(data: np.ndarray) -> np.ndarray:
    if data.ndim == 1:
        return data.reshape(1, -1).astype(np.int64, copy=False)
    return data.astype(np.int64, copy=False)


def _normalize_points(points: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError("points must have shape (n_points, 3)")
    return points


def _normalize_cells(cells: CellDict) -> List[Tuple[str, np.ndarray]]:
    cell_blocks: List[Tuple[str, np.ndarray]] = []
    for cell_type, data in cells.items():
        if cell_type not in _CELL_TYPE_MAP:
            raise ValueError(f"Unsupported cell type: {cell_type}")
        array = _as_2d_int_array(np.asarray(data))
        cell_blocks.append((cell_type, array))
    return cell_blocks


def _build_pv_mesh(points: np.ndarray, cell_blocks: List[Tuple[str, np.ndarray]]) -> pv.DataSet:
    if not cell_blocks:
        return pv.PolyData(points)

    cell_array_parts: List[np.ndarray] = []
    cell_types: List[np.ndarray] = []

    for cell_type, data in cell_blocks:
        n_cells, n_nodes = data.shape
        counts = np.full((n_cells, 1), n_nodes, dtype=np.int64)
        cell_array_parts.append(np.hstack([counts, data]).ravel())
        vtk_cell_type = _CELL_TYPE_MAP[cell_type]
        cell_types.append(np.full(n_cells, int(vtk_cell_type), dtype=np.int64))

    cells = np.concatenate(cell_array_parts) if cell_array_parts else np.array([], dtype=np.int64)
    celltypes = np.concatenate(cell_types) if cell_types else np.array([], dtype=np.int64)
    return pv.UnstructuredGrid(cells, celltypes, points)


class Mesh(VtkMeshOpsMixin):
    """Minimal mesh wrapper exposing pyvista and meshio I/O."""

    def __init__(
        self,
        points: np.ndarray,
        cells: CellDict,
        point_data: Optional[PointData] = None,
        cell_data: Optional[CellDataInput] = None,
    ) -> None:
        self._points = _normalize_points(points)
        self._cell_blocks = _normalize_cells(cells)
        self._cells: Dict[str, np.ndarray] = {cell_type: data for cell_type, data in self._cell_blocks}
        self._point_data = {k: np.asarray(v) for k, v in (point_data or {}).items()}
        self._cell_data_blocks = self._normalize_cell_data(cell_data or {}, len(self._cell_blocks))
        self._pv_mesh = _build_pv_mesh(self._points, self._cell_blocks)
        self.pointLocator = None
        self.cellLocator = None

    @staticmethod
    def _normalize_cell_data(
        cell_data: CellDataInput, block_count: int
    ) -> Dict[str, List[np.ndarray]]:
        if not cell_data:
            return {}
        normalized: Dict[str, List[np.ndarray]] = {}
        for name, data in cell_data.items():
            if isinstance(data, (list, tuple)):
                if block_count and len(data) != block_count:
                    raise ValueError(
                        f"cell_data for '{name}' must have {block_count} blocks"
                    )
                normalized[name] = [np.asarray(block) for block in data]
            else:
                if block_count > 1:
                    raise ValueError(
                        f"cell_data for '{name}' must be a list for multi-block meshes"
                    )
                normalized[name] = [np.asarray(data)]
        return normalized

    @property
    def pv_mesh(self) -> pv.DataSet:
        """Underlying pyvista mesh."""
        return self._pv_mesh

    @property
    def points(self) -> np.ndarray:
        """Point coordinates as array of shape (n_points, 3)."""
        return self._points

    @property
    def cells(self) -> Dict[str, np.ndarray]:
        """Mesh cells as a dict of arrays keyed by cell type."""
        return self._cells

    @property
    def point_data(self) -> Dict[str, np.ndarray]:
        """Point data arrays keyed by name."""
        return self._point_data

    @property
    def cell_data(self) -> Dict[str, Union[np.ndarray, List[np.ndarray]]]:
        """Cell data arrays keyed by name.

        Returns arrays directly for single-block meshes, otherwise lists of arrays
        aligned to the cell blocks.
        """
        if len(self._cell_blocks) <= 1:
            return {k: v[0] for k, v in self._cell_data_blocks.items()}
        return {k: list(v) for k, v in self._cell_data_blocks.items()}

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        cell_counts = {cell_type: data.shape[0] for cell_type, data in self._cells.items()}
        bounds = self._pv_mesh.bounds
        bounds_text = "(" + ", ".join(f"{value:.6g}" for value in bounds) + ")"

        if self._point_data:
            point_data_text = ", ".join(
                f"{name}: {data.shape}" for name, data in self._point_data.items()
            )
        else:
            point_data_text = "None"

        if self._cell_data_blocks:
            parts = []
            for name, blocks in self._cell_data_blocks.items():
                if len(blocks) == 1:
                    shape = blocks[0].shape
                else:
                    shape = [block.shape for block in blocks]
                parts.append(f"{name}: {shape}")
            cell_data_text = ", ".join(parts)
        else:
            cell_data_text = "None"

        lines = [
            "Mesh(",
            f"  n_points={self._points.shape[0]}, n_cells={self._pv_mesh.n_cells}",
            f"  bounds={bounds_text}",
            f"  cell_types={cell_counts}",
            f"  point_data={point_data_text}",
            f"  cell_data={cell_data_text}",
            ")",
        ]
        return "\n".join(lines)

    @classmethod
    def tetra_cells_from_pv(cls, grid: pv.UnstructuredGrid) -> "Mesh":
        """Build a Mesh from a pyvista UnstructuredGrid with tetra cells."""
        cells = grid.cells.reshape(-1, 5)
        if not np.all(cells[:, 0] == 4):
            raise ValueError("Expected tetra cells.")
        tetra = cells[:, 1:5]
        return cls(points=grid.points, cells={"tetra": tetra})

    @classmethod
    def triangle_faces_from_pv(cls, surface: pv.PolyData) -> "Mesh":
        """Build a Mesh from a pyvista PolyData surface with triangles."""
        faces = surface.faces.reshape(-1, 4)
        if not np.all(faces[:, 0] == 3):
            raise ValueError("Expected triangle faces.")
        triangles = faces[:, 1:4]
        return cls(points=surface.points, cells={"triangle": triangles})

    @classmethod
    def load(cls, path: Union[str, Path]) -> "Mesh":
        """Load mesh from file using meshio."""
        mesh = meshio.read(Path(path))
        cells_by_type: Dict[str, List[np.ndarray]] = {}
        cell_data_by_type: Dict[str, Dict[str, List[np.ndarray]]] = {}

        for block_index, block in enumerate(mesh.cells):
            cell_type = block.type
            data = np.asarray(block.data)
            cells_by_type.setdefault(cell_type, []).append(data)

            for name, data_list in mesh.cell_data.items():
                cell_data_by_type.setdefault(name, {}).setdefault(cell_type, []).append(
                    np.asarray(data_list[block_index])
                )

        cells: Dict[str, np.ndarray] = {}
        for cell_type, blocks in cells_by_type.items():
            cells[cell_type] = np.concatenate(blocks, axis=0) if len(blocks) > 1 else blocks[0]

        cell_data_blocks: Dict[str, List[np.ndarray]] = {}
        for name, per_type in cell_data_by_type.items():
            blocks_per_type: List[np.ndarray] = []
            for cell_type in cells.keys():
                blocks = per_type.get(cell_type, [])
                if not blocks:
                    blocks_per_type.append(np.empty((0,), dtype=float))
                elif len(blocks) == 1:
                    blocks_per_type.append(blocks[0])
                else:
                    blocks_per_type.append(np.concatenate(blocks, axis=0))
            cell_data_blocks[name] = blocks_per_type

        return cls(
            points=mesh.points,
            cells=cells,
            point_data=mesh.point_data,
            cell_data=cell_data_blocks,
        )

    def save(self, path: Union[str, Path]) -> None:
        """Save mesh to file using meshio."""
        if self._cell_data_blocks:
            cell_data = self._cell_data_blocks
        else:
            cell_data = None
        mesh = meshio.Mesh(
            points=self._points,
            cells=self._cell_blocks,
            point_data=self._point_data or None,
            cell_data=cell_data,
        )
        meshio.write(Path(path), mesh)

    def remesh_volume(
        self, mmg_args: Optional[Union[Sequence[str], "MmgOptions"]] = None
    ) -> "Mesh":
        """Remesh a 3D volume mesh using pymmg/mmg3d."""
        from gdmesh.remesh import MmgOptions, remesh_volume

        if isinstance(mmg_args, MmgOptions):
            mmg_args = mmg_args.to_args()

        return remesh_volume(self, mmg_args=mmg_args)

    def remesh_surface(
        self, mmg_args: Optional[Union[Sequence[str], "MmgOptions"]] = None
    ) -> "Mesh":
        """Remesh a 3D surface mesh using pymmg/mmgs."""
        from gdmesh.remesh import MmgOptions, remesh_surface

        if isinstance(mmg_args, MmgOptions):
            mmg_args = mmg_args.to_args()

        return remesh_surface(self, mmg_args=mmg_args)

    def remesh_2d(self, mmg_args: Optional[Union[Sequence[str], "MmgOptions"]] = None) -> "Mesh":
        """Remesh a 2D mesh using pymmg/mmg2d."""
        from gdmesh.remesh import MmgOptions, remesh_2d

        if isinstance(mmg_args, MmgOptions):
            mmg_args = mmg_args.to_args()

        return remesh_2d(self, mmg_args=mmg_args)

    def boundary_edges(self, mesh_for_ids=None, rev: bool = True):
        """Return boundary edge loops for an open surface mesh."""
        from gdmesh.boundary_edges import get_boundary_edges

        return get_boundary_edges(self, mesh_for_ids=mesh_for_ids, rev=rev)
