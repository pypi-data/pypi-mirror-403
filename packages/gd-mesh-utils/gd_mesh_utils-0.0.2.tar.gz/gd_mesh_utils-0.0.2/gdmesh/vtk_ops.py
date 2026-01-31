"""VTK-specific mesh operations for spatial queries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from vtkmodules.vtkCommonCore import mutable, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellLocator, vtkPointLocator, vtkPolyData
from vtkmodules.vtkFiltersGeneral import vtkOBBTree
from vtkmodules.vtkFiltersGeometry import vtkGeometryFilter
from vtkmodules.util.numpy_support import vtk_to_numpy


@dataclass(frozen=True)
class PairIdCoord:
    idx: int
    coord: np.ndarray


class Points:
    def __init__(self, points: Optional[vtkPoints] = None) -> None:
        self._points = points if points is not None else vtkPoints()

    @property
    def vtk_points(self) -> vtkPoints:
        return self._points

    def __len__(self) -> int:
        return int(self._points.GetNumberOfPoints())

    def as_np(self) -> np.ndarray:
        if self._points.GetNumberOfPoints() == 0:
            return np.empty((0, 3), dtype=float)
        data = self._points.GetData()
        if data is None:
            return np.empty((0, 3), dtype=float)
        array = vtk_to_numpy(data)
        if array.size == 0:
            return np.empty((0, 3), dtype=float)
        return array.reshape(-1, 3)


class VtkMeshOpsMixin:
    pointLocator: Optional[vtkPointLocator]
    cellLocator: Optional[vtkCellLocator]

    def _vtk_dataset(self):
        if hasattr(self, "_pv_mesh"):
            return self._pv_mesh
        return self.pv_mesh

    def _vtk_polydata(self) -> vtkPolyData:
        dataset = self._vtk_dataset()
        if isinstance(dataset, vtkPolyData):
            return dataset
        if hasattr(dataset, "extract_surface"):
            return dataset.extract_surface()
        geometry = vtkGeometryFilter()
        geometry.SetInputData(dataset)
        geometry.Update()
        return geometry.GetOutput()

    def intersect(self, point_1, point_2):
        """
        Computes the intersection of the mesh with the line defined by two points.

        :param point_1: First point of the line (list or np.array, of size 3)
        :param point_2: Second point of the line (list or np.array, of size 3)

        :return: Coordinates of n intersection points
        """
        tree = vtkOBBTree()
        tree.SetDataSet(self._vtk_polydata())
        tree.BuildLocator()
        intersect_points = Points()
        tree.IntersectWithLine(point_1, point_2, intersect_points.vtk_points, None)
        return intersect_points.as_np()

    def buildPointLocator(self):
        self.pointLocator = vtkPointLocator()
        self.pointLocator.SetDataSet(self._vtk_dataset())
        self.pointLocator.BuildLocator()

    def buildCellLocator(self):
        self.cellLocator = vtkCellLocator()
        self.cellLocator.SetDataSet(self._vtk_dataset())
        self.cellLocator.BuildLocator()

    def closestPoint(self, point) -> "PairIdCoord":
        """
        Return the id and coordinates of the closest point to `point` in the mesh

        :param point: Coordinates of a point

        :return: Index and coordinates of nearest mesh point
        """
        if getattr(self, "pointLocator", None) is None:
            self.buildPointLocator()
        idx = self.pointLocator.FindClosestPoint(point)
        return PairIdCoord(int(idx), np.array(self._vtk_dataset().GetPoint(idx)))

    def closestCell(self, point) -> "PairIdCoord":
        """
        Return the id of the closest cell to `point` in the mesh

        :param point: Coordinates of a point

        :return: Index of nearest mesh cell
        """
        if getattr(self, "cellLocator", None) is None:
            self.buildCellLocator()

        closest_point = [0.0, 0.0, 0.0]
        cell_id = mutable(0)
        sub_id = mutable(0)
        dist2 = mutable(0.0)

        self.cellLocator.FindClosestPoint(point, closest_point, cell_id, sub_id, dist2)
        return PairIdCoord(int(cell_id), np.array(closest_point, dtype=float))
