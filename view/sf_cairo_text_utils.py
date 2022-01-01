import cairo


def add_text_by_center(cr: cairo.Context, text, y, xl=0, xr=1):
    te = cr.text_extents(text)
    x = xl + (xr - xl - te.width) / 2
    cr.move_to(x, y)
    cr.show_text(text)
    cr.stroke()


def add_text_by_right(cr: cairo.Context, text, y, xl=0, xr=1):
    te = cr.text_extents(text)
    x = xr - te.width
    cr.move_to(x, y)
    cr.show_text(text)
    cr.stroke()
