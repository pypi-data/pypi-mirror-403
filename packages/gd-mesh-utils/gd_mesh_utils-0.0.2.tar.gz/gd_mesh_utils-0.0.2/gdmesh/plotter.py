import logging

import pyvista as pv

default_theme = pv.themes.DocumentTheme()
default_theme.background = "white"
default_theme.color = "lightgrey"
default_theme.show_edges = True


class Plotter(pv.Plotter):
    def __init__(self, **kwargs):
        # title, off_screen, window_size, theme
        theme = kwargs.pop("theme", default_theme)
        super().__init__(theme=theme, **kwargs)

    def add_mesh(self, mesh, *args, **kwargs):
        if hasattr(mesh, "pv_mesh"):
            mesh = mesh.pv_mesh
        # kwargs.setdefault("show_edges", True)
        return super().add_mesh(mesh, *args, **kwargs)

    def save(self, fname: str):
        return self.screenshot(fname)

    def __enter__(self) -> "Plotter":
        # self.add_key_event("Escape", self.close)  # A/Q/E pour fermer
        self.add_key_event("c", lambda: print(self.camera_position))
        self.add_camera_orientation_widget()
        return self

    def __getitem__(self, item) -> "Plotter":
        if isinstance(item, tuple):
            self.subplot(*item)
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        if exc_type is None:
            self.show()
        self.close()
        return False

    # def __exit__(self, exc_type, exc, traceback) -> bool:
    #     if exc_type is None:
    #         try:
    #             self.show()
    #         except AttributeError:
    #             pass
    #     try:
    #         self.close()
    #     except AttributeError:
    #         pass
    #     return False


log = logging.getLogger(__name__)
