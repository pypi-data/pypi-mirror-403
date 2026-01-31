"""Boundary edge extraction for open surface meshes."""

from __future__ import annotations

import logging
import warnings
from typing import Any, List, Optional

import numpy as np
import pyvista as pv
from vtkmodules.vtkFiltersCore import vtkCellDataToPointData, vtkPolyDataConnectivityFilter

logger = logging.getLogger(__name__)


def _as_polydata(mesh) -> pv.PolyData:
    if hasattr(mesh, "pv_mesh"):
        mesh = mesh.pv_mesh
    poly = pv.wrap(mesh)
    if not isinstance(poly, pv.PolyData):
        poly = poly.extract_surface()
    return poly


def _closest_point_index(mesh_for_ids, point) -> int:
    if hasattr(mesh_for_ids, "closestPoint"):
        result = mesh_for_ids.closestPoint(point)
        if hasattr(result, "idx"):
            return int(result.idx)
        return int(result[0])
    if hasattr(mesh_for_ids, "find_closest_point"):
        return int(mesh_for_ids.find_closest_point(point))
    raise TypeError("mesh_for_ids must provide closestPoint or find_closest_point.")


def _lines_from_polydata(polydata) -> np.ndarray:
    lines = pv.wrap(polydata).lines
    if lines.size == 0:
        return np.empty((0, 2), dtype=np.int64)
    lines = lines.reshape(-1, 3)
    return lines[:, 1:3].astype(np.int64, copy=False)


def _connectivity_regions(polydata) -> pv.PolyData:
    connectivity = vtkPolyDataConnectivityFilter()
    connectivity.SetInputData(polydata)
    connectivity.SetExtractionModeToAllRegions()
    connectivity.ColorRegionsOn()
    connectivity.Update()
    connected = connectivity.GetOutput()

    if connected.GetPointData().GetArray("RegionId") is None:
        cell_to_point = vtkCellDataToPointData()
        cell_to_point.SetInputData(connected)
        cell_to_point.PassCellDataOn()
        cell_to_point.Update()
        connected = cell_to_point.GetOutput()

    return connected


def get_boundary_edges(
    mesh: Any,
    mesh_for_ids: Optional[Any] = None,
    rev: bool = True,
) -> List[List[List[int]]]:
    """
    Return the boundary edge loops of an open surface mesh.

    Args:
        mesh: The input mesh (surface data).
        mesh_for_ids: Optional mesh used to resolve point ids for the returned
            edges. Defaults to the same mesh.
        rev: Whether to return each loop in reverse order.

    Returns:
        List of loops; each loop is a list of [point_id, point_id] edges forming
        a closed boundary.
    """
    boundary_edges = []
    surface = _as_polydata(mesh)

    if mesh_for_ids is None:
        mesh_for_ids = mesh

    edges = surface.extract_feature_edges(
        boundary_edges=True,
        feature_edges=False,
        non_manifold_edges=False,
        manifold_edges=False,
    )
    connected = _connectivity_regions(edges)
    connected = pv.wrap(connected)

    points = connected.points
    rId = connected.point_data.get("RegionId")
    if rId is None:
        raise RuntimeError("RegionId array not found on boundary edges.")
    nb_holes = len(np.unique(rId))
    logger.debug(f"Found {nb_holes} hole{'s' if nb_holes > 1 else ''}")

    lines = _lines_from_polydata(connected)
    for i in range(nb_holes):
        couples = []
        for line in lines:
            if rId[line[0]] == i and rId[line[1]] == i:
                couples.append(
                    [_closest_point_index(mesh_for_ids, points[p_id]) for p_id in line]
                )

        boundary_edges.append(_chain(couples, rev=rev))

    return boundary_edges


def getBoundaryEdges(endo, mesh_for_ids=None, rev=True):
    """Deprecated. Use :func:`get_boundary_edges` instead."""
    warnings.warn(
        "getBoundaryEdges is deprecated, use get_boundary_edges instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_boundary_edges(endo, mesh_for_ids=mesh_for_ids, rev=rev)


def _chain(couples, rev=True):
    """Sort a list of (a, b) edge pairs into a single ordered path (internal helper).
    Works on a copy of the input; the original list is not modified.
    """
    couples = list(couples)

    if rev:
        seed = couples[0][0]
        ordered_couples = [list(reversed(couples.pop(0)))]
    else:
        seed = couples[0][1]
        ordered_couples = [couples.pop(0)]

    ite, ite_max = 0, len(couples) + 1
    while len(couples) > 0:
        ite += 1
        for i, c in enumerate(couples):
            if c[0] == seed:
                seed = c[1]
                ordered_couples.append(couples.pop(i))
            elif c[1] == seed:
                seed = c[0]
                ordered_couples.append(list(reversed(couples.pop(i))))

        assert (
            ite < ite_max
        ), f"Could not find a unique path,\ncouples: {couples}\nordered_couples: {ordered_couples}"

    return ordered_couples
