import logging
import numpy as np
import pyvista as pv

import gdutils as gd
import gdmesh as gm


def main():
    out = gd.fPath(__file__, "out")

    with gd.Container(out) as ct:
        cube = pv.Cube().triangulate()
        triangles = cube.faces.reshape(-1, 4)[:, 1:4]
        mesh = gm.Mesh(points=cube.points, cells={"triangle": triangles})

        point_1 = np.array([-1.2, 0.0, 0.0])
        point_2 = np.array([1.2, 0.0, 0.0])

        intersections = mesh.intersect(point_1, point_2)
        if intersections.size == 0:
            raise RuntimeError("No intersection found between line and cube.")
        intersection = intersections[0]

        line = pv.Line(point_1, point_2)
        points = pv.PolyData(np.vstack([point_1, point_2]))
        intersection_point = pv.PolyData(intersection.reshape(1, 3))

        with gm.Plotter() as p:
            p.add_mesh(cube, color="lightgray", opacity=0.5)
            p.add_mesh(line, color="blue", line_width=3)
            p.add_mesh(points, color="red", point_size=15, render_points_as_spheres=True)
            p.add_mesh(
                intersection_point,
                color="gold",
                point_size=20,
                render_points_as_spheres=True,
            )
            # p.add_axes()
            # p.save(ct / "intersect_cube.png")

    log.info("Saved intersection example.")


log = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    log = gd.get_logger()

    main()
