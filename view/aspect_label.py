import math

from math import pi

import cairo
from flatlib import const

from view.sf_geometry import rotate_point


class AspectLabelDrawer:
    def draw_aspect(self, aspect, cr: cairo.Context, default_color: bool = True):
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        ASPECT_TO_LABEL_FOO[aspect](cr, default_color)

    def set_aspect_color(self, aspect, cr: cairo.Context):
        if aspect in [const.OPPOSITION, const.SQUARE]:
            cr.set_source_rgb(0.5, 0.1, 0.1)
        elif aspect in [const.TRINE, const.SEXTILE]:
            cr.set_source_rgb(0.1, 0.5, 0.1)
        elif aspect in [const.CONJUNCTION]:
            cr.set_source_rgb(0.1, 0.1, 0.5)


def draw_opposition(cr: cairo.Context, default_color: True):
    if default_color:
        cr.set_source_rgb(0.5, 0.1, 0.1)

    cr.arc(0.8, 0.2, 0.2, 0, 2 * math.pi)
    cr.stroke()
    cr.arc(0.2, 0.8, 0.2, 0, 2 * math.pi)
    cr.stroke()
    cr.move_to(0.4, 0.6)
    cr.line_to(0.6, 0.4)
    cr.stroke()


def draw_trine(cr: cairo.Context, default_color: True):
    if default_color:
        cr.set_source_rgb(0.1, 0.5, 0.1)

    cr.move_to(0.5, 0)
    cr.line_to(1, 1)
    cr.line_to(0, 1)
    cr.line_to(0.5, 0)
    cr.stroke()


def draw_square(cr: cairo.Context, default_color: True):
    if default_color:
        cr.set_source_rgb(0.5, 0.1, 0.1)
    cr.move_to(0, 0)
    cr.line_to(1, 0)
    cr.line_to(1, 1)
    cr.line_to(0, 1)
    cr.line_to(0, 0)
    cr.stroke()


def draw_sextile(cr: cairo.Context, default_color: True):
    if default_color:
        cr.set_source_rgb(0.1, 0.5, 0.1)

    cr.move_to(0.5, 0)
    cr.line_to(0.5, 1)
    cr.stroke()
    cr.move_to(0.95, 0.25)
    cr.line_to(0.05, 0.75)
    cr.stroke()
    cr.move_to(0.05, 0.25)
    cr.line_to(0.95, 0.75)
    cr.stroke()


def draw_conjunction(cr: cairo.Context, default_color: True):
    if default_color:
        cr.set_source_rgb(0.1, 0.1, 0.5)

    cr.arc(0.3, 0.7, 0.3, 0, 2 * math.pi)
    cr.stroke()
    cr.move_to(0.5, 0.5)
    cr.line_to(1, 0)
    cr.stroke()


ASPECT_TO_LABEL_FOO = {
    const.CONJUNCTION: draw_conjunction,
    const.SEXTILE: draw_sextile,
    const.SQUARE: draw_square,
    const.TRINE: draw_trine,
    const.OPPOSITION: draw_opposition
}
