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

        query_point = np.array([1.2, 0.2, -0.1])
        closest = mesh.closestPoint(query_point)

        query_poly = pv.PolyData(query_point.reshape(1, 3))
        closest_poly = pv.PolyData(closest.coord.reshape(1, 3))
        line = pv.Line(query_point, closest.coord)

        with gm.Plotter() as p:
            p.add_mesh(cube, color="lightgray", opacity=0.5)
            p.add_mesh(query_poly, color="red", point_size=15, render_points_as_spheres=True)
            p.add_mesh(
                closest_poly,
                color="gold",
                point_size=20,
                render_points_as_spheres=True,
            )
            p.add_mesh(line, color="blue", line_width=3)
        # plotter.add_axes()
        # plotter.save(ct / "closest_point_cube.png")
        # plotter.close()

    log.info("Saved closest point example.")


log = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    log = gd.get_logger()

    main()
