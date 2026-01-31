import logging

import pyvista as pv

import gdutils as gd
import gdmesh as gm


def ex_tetra():
    out = gd.fPath(__file__, "out")
    with gd.Container(out / "remesh_cube", clean=True) as ct:
        cube = pv.Cube().triangulate().delaunay_3d()
        mesh = gm.Mesh.tetra_cells_from_pv(cube)
        mesh.save(input_path := ct / "input.vtk")

        mmg_args = gm.MmgOptions(hmax=0.25, hmin=0.05, hausd=0.01, hgrad=1.3)
        log.info("MMG options: %s", " ".join(mmg_args.to_args()))

        remeshed = mesh.remesh_volume(mmg_args=mmg_args)
        remeshed.save(output_path := ct / "output.vtk")

        plotter = pv.Plotter(shape=(1, 2), off_screen=False)
        plotter.subplot(0, 0)
        plotter.add_text("Input", font_size=10)
        plotter.add_mesh(mesh.pv_mesh, color="lightgray", show_edges=True)
        plotter.subplot(0, 1)
        plotter.add_text("Remeshed", font_size=10)
        plotter.add_mesh(remeshed.pv_mesh, color="lightgray", show_edges=True)
        # plotter.screenshot(ct / "input_vs_output.png")
        plotter.link_views()
        plotter.show()
        plotter.close()

        log.info("Input mesh: %s", input_path)
        log.info("Output mesh: %s", output_path)


def ex_tri():
    out = gd.fPath(__file__, "out")
    with gd.Container(out / "remesh_surface", clean=True) as ct:
        surface = pv.Cube().triangulate()
        mesh = gm.Mesh.triangle_faces_from_pv(surface)
        mesh.save(input_path := ct / "input.vtk")

        mmg_args = gm.MmgOptions(hmax=0.3, hmin=0.05, hausd=0.01, hgrad=1.3)
        log.info("MMGS options: %s", " ".join(mmg_args.to_args()))

        remeshed = mesh.remesh_surface(mmg_args)
        remeshed.save(output_path := ct / "output.vtk")

        with gm.Plotter(title="oui", shape=(1, 2), off_screen=True) as p:
            p[0, 0].add_mesh(mesh)
            p[0, 1].add_mesh(remeshed)
            p.link_views()
            p.save(ct / "out.png")


log = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    log = gd.get_logger()

    ex_tetra()
    # ex_tri()

    # out = gd.fPath(__file__, "out")
    # with gd.Container(out / "remesh_cube") as ct:
    #     print(gm.Mesh.load(ct.input))
