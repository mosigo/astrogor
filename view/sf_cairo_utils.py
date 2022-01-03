from abc import abstractmethod

import cairo


class CairoDrawer:

    @abstractmethod
    def draw(self, cr: cairo.Context):
        pass


def add_text_by_center(cr: cairo.Context, text, y, xl=0, xr=1):
    te = cr.text_extents(text)
    x = xl + (xr - xl - te.width) / 2
    cr.move_to(x, y)
    cr.show_text(text)
    cr.stroke()


def add_text_by_right(cr: cairo.Context, text, y, xr=1):
    te = cr.text_extents(text)
    x = xr - te.width
    cr.move_to(x, y)
    cr.show_text(text)
    cr.stroke()


def save_to_pdf(out_file_path, width, height, drawer: CairoDrawer):
    surface_pdf = cairo.PDFSurface(out_file_path, width, height)
    surface_pdf.set_fallback_resolution(500, 500)
    cr = cairo.Context(surface_pdf)

    cr.scale(width, width)
    drawer.draw(cr)

    surface_pdf.finish()
