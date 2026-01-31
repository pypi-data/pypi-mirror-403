"""Remeshing utilities using pymmg and subprocess."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from typing import Optional, Sequence, TYPE_CHECKING

import numpy as np
import meshio

from gdutils.datacontainer.temp import TempContainer

if TYPE_CHECKING:
    from gdmesh.mesh import Mesh


@dataclass(frozen=True)
class MmgOptions:
    hmax: float
    hmin: float
    hausd: float
    hgrad: float

    def to_args(self) -> list[str]:
        return [
            "-hmax",
            str(self.hmax),
            "-hmin",
            str(self.hmin),
            "-hausd",
            str(self.hausd),
            "-hgrad",
            str(self.hgrad),
        ]


def _run_mmg(
    module_name: str,
    input_path,
    output_path,
    mmg_args: list[str],
    tool_label: str,
) -> None:
    """Run an mmg subprocess (mmg3d, mmgs, or mmg2d). Raises RuntimeError on non-zero exit."""
    cmd = [sys.executable, "-m", module_name, str(input_path), str(output_path), *mmg_args]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        raise RuntimeError(
            f"{tool_label} failed with exit code "
            f"{process.returncode}\nstdout:\n{stdout}\nstderr:\n{stderr}"
        )


def remesh_volume(mesh: "Mesh", mmg_args: Optional[Sequence[str]] = None) -> "Mesh":
    """Run mmg3d on a mesh and return a new Mesh."""
    mmg_args = list(mmg_args or [])
    with TempContainer() as ct:
        input_path = ct / "input.mesh"
        output_path = ct / "output.mesh"
        mesh.save(input_path)
        _run_mmg("mmg3d", input_path, output_path, mmg_args, "mmg3d")
        return mesh.__class__.load(output_path)


def remesh_surface(mesh: "Mesh", mmg_args: Optional[Sequence[str]] = None) -> "Mesh":
    """Run mmgs on a surface mesh and return a new Mesh."""
    mmg_args = list(mmg_args or [])
    with TempContainer() as ct:
        input_path = ct / "input.mesh"
        output_path = ct / "output.mesh"
        mesh.save(input_path)
        _run_mmg("mmgs", input_path, output_path, mmg_args, "mmgs")
        return mesh.__class__.load(output_path)


def remesh_2d(mesh: "Mesh", mmg_args: Optional[Sequence[str]] = None) -> "Mesh":
    """Run mmg2d on a 2D mesh and return a new Mesh."""
    mmg_args = list(mmg_args or [])
    with TempContainer() as ct:
        input_path = ct / "input.mesh"
        output_path = ct / "output.mesh"

        points = mesh.points[:, :2]
        cells = [(cell_type, np.asarray(data)) for cell_type, data in mesh.cells.items()]
        meshio.write(input_path, meshio.Mesh(points=points, cells=cells))
        _run_mmg("mmg2d", input_path, output_path, mmg_args, "mmg2d")

        remeshed = meshio.read(output_path)
        points = remeshed.points
        if points.ndim == 2 and points.shape[1] == 2:
            points = np.hstack([points, np.zeros((points.shape[0], 1), dtype=points.dtype)])

        cells_by_type = {}
        cell_data_by_type = {}
        for block_index, block in enumerate(remeshed.cells):
            cell_type = block.type
            data = np.asarray(block.data)
            cells_by_type.setdefault(cell_type, []).append(data)

            for name, data_list in remeshed.cell_data.items():
                cell_data_by_type.setdefault(name, {}).setdefault(cell_type, []).append(
                    np.asarray(data_list[block_index])
                )

        cells = {}
        for cell_type, blocks in cells_by_type.items():
            cells[cell_type] = np.concatenate(blocks, axis=0) if len(blocks) > 1 else blocks[0]

        cell_data_blocks = {}
        for name, per_type in cell_data_by_type.items():
            blocks_per_type = []
            for cell_type in cells.keys():
                blocks = per_type.get(cell_type, [])
                if not blocks:
                    blocks_per_type.append(np.empty((0,), dtype=float))
                elif len(blocks) == 1:
                    blocks_per_type.append(blocks[0])
                else:
                    blocks_per_type.append(np.concatenate(blocks, axis=0))
            cell_data_blocks[name] = blocks_per_type

        return mesh.__class__(
            points=points,
            cells=cells,
            point_data=remeshed.point_data,
            cell_data=cell_data_blocks,
        )
