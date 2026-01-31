import logging
import numpy as np
import pyvista as pv

import gdutils as gd
import gdmesh as gm


def _loops_to_polydata(points: np.ndarray, loops: list[list[list[int]]]) -> pv.PolyData:
    if not loops:
        return pv.PolyData()

    line_parts = []
    for loop in loops:
        ordered = [loop[0][0]] + [edge[1] for edge in loop]
        line_parts.append(np.hstack([len(ordered), np.array(ordered, dtype=np.int64)]))

    lines = np.concatenate(line_parts)
    return pv.PolyData(points, lines=lines)


def main():
    out = gd.fPath(__file__, "out")

    with gd.Container(out) as ct:
        sphere = pv.Sphere(radius=10.0, theta_resolution=50, phi_resolution=10)
        sphere.point_data["z"] = (sphere.points[:, 2] < 0).astype(int)

        hemisphere = sphere.threshold((0.5, 1.5), scalars="z")
        hemisphere.save(ct / "hemisphere_1.vtk")
        surface = hemisphere.extract_surface().triangulate()

        mesh = gm.Mesh.triangle_faces_from_pv(surface)
        loops = mesh.boundary_edges()
        log.info("Found %s boundary loops.", len(loops))
        boundary_lines = _loops_to_polydata(mesh.points, loops)

        with gm.Plotter() as p:
            p.add_mesh(surface, color="lightgray", opacity=0.5)
            if boundary_lines.n_points > 0:
                p.add_mesh(boundary_lines, color="tomato", line_width=4)
            

    log.info("Saved boundary edges example.")


log = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    log = gd.get_logger()

    main()
