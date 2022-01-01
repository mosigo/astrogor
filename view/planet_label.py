import math

from math import pi

import cairo
from flatlib import const

from view.sf_geometry import rotate_point


class PlanetLabelDrawer:
    def draw_planet(self, planet, cr):
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        PLANET_TO_LABEL_FOO[planet](cr)


def draw_sun(cr):
    cr.arc(0.5, 0.5, 0.5, 0, 2 * pi)
    cr.stroke()
    cr.arc(0.5, 0.5, 0.05, 0, 2 * pi)
    cr.fill()


def draw_moon(cr):
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.arc(0.5, 0.5, 0.5, -45 * pi / 64, 45 * pi / 64)
    cr.stroke()
    cr.arc(0.2, 0.5, 0.4, -pi / 2, pi / 2)
    cr.stroke()


def draw_mercury(cr):
    cr.arc(0.5, 0.41, 0.24, 0, 2 * pi)
    cr.stroke()
    cr.move_to(0.5, 0.7)
    cr.line_to(0.5, 1)
    cr.stroke()
    cr.move_to(0.3, 0.85)
    cr.line_to(0.7, 0.85)
    cr.stroke()
    cr.arc(0.5, -0.14, 0.3, pi / 6, pi - pi / 6)
    cr.stroke()


def draw_venus(cr):
    cr.arc(0.5, 0.3, 0.3, 0, 2 * pi)
    cr.stroke()
    cr.move_to(0.5, 0.6)
    cr.line_to(0.5, 1)
    cr.stroke()
    cr.move_to(0.3, 0.8)
    cr.line_to(0.7, 0.8)
    cr.stroke()


def draw_mars(cr):
    right_top_corner = (0.85, 0.15)
    cr.arc(0.3, 0.7, 0.3, 0, 2 * pi)
    cr.stroke()
    cr.move_to(0.51, 0.49)
    cr.line_to(*right_top_corner)
    cr.stroke()
    cr.move_to(0.6, right_top_corner[1])
    cr.line_to(*right_top_corner)
    cr.stroke()
    cr.move_to(right_top_corner[0], 0.4)
    cr.line_to(*right_top_corner)
    cr.stroke()


def draw_jupiter(cr):
    cr.arc(0.2, 0.25, 0.25, -pi / 2, pi / 2)
    cr.stroke()

    cr.move_to(0.2, 0.5)
    cr.line_to(0.8, 0.5)
    cr.stroke()

    cr.move_to(0.7, 0.25)
    cr.line_to(0.7, 1)
    cr.stroke()


def draw_saturn(cr):
    cr.arc(0.5, 0.75, 0.25, -3 * pi / 4, 3 * pi / 4)
    cr.stroke()

    cr.move_to(0.06, 0.29)
    cr.line_to(0.60, 0.29)
    cr.stroke()

    cr.move_to(0.33, 0)
    cr.line_to(0.33, 0.58)
    cr.stroke()


def draw_uranus(cr):
    cr.arc(0.5, 0.75, 0.2, 0, 2 * pi)
    cr.stroke()

    cr.move_to(0.5, 0)
    cr.line_to(0.5, 0.5)
    cr.stroke()

    cr.move_to(0.25, 0.05)
    cr.line_to(0.25, 0.45)
    cr.stroke()

    cr.move_to(0.75, 0.05)
    cr.line_to(0.75, 0.45)
    cr.stroke()

    cr.move_to(0.25, 0.25)
    cr.line_to(0.75, 0.25)
    cr.stroke()


def draw_neptune(cr):
    cr.arc(0.5, 0.1, 0.35, 0, pi)
    cr.stroke()

    cr.move_to(0.25, 0.7)
    cr.line_to(0.75, 0.7)
    cr.stroke()

    cr.move_to(0.5, 0.1)
    cr.line_to(0.5, 1)
    cr.stroke()


def draw_pluto(cr):
    cr.arc(0.5, 0.2, 0.2, 0, 2 * pi)
    cr.stroke()
    cr.arc(0.5, 0.23, 0.35, 0, pi)
    cr.stroke()
    cr.move_to(0.5, 0.58)
    cr.line_to(0.5, 1)
    cr.stroke()
    cr.move_to(0.3, 0.8)
    cr.line_to(0.7, 0.8)
    cr.stroke()


def draw_chiron(cr):
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.arc(0.5, 0.75, 0.25, 0, 2 * pi)
    cr.stroke()

    cr.move_to(0.5, 0)
    cr.line_to(0.5, 0.5)
    cr.stroke()

    cr.move_to(0.5, 0.25)
    cr.line_to(0.75, 0)
    cr.stroke()

    cr.move_to(0.5, 0.25)
    cr.line_to(0.75, 0.48)
    cr.stroke()


def draw_north_node(cr: cairo.Context):
    cr.move_to(0.4, 0.8)
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.curve_to(-0.2, -0.2, 1.2, -0.2, 0.6, 0.8)
    cr.stroke()

    cr.arc(0.31, 0.85, 0.1, 0, 2 * math.pi)
    cr.stroke()

    cr.arc(0.69, 0.85, 0.1, 0, 2 * math.pi)
    cr.stroke()


def draw_south_node(cr: cairo.Context):
    cr.move_to(0.6, 0.2)
    cr.curve_to(1.2, 1.2, -0.2, 1.2, 0.4, 0.2)
    cr.stroke()

    cr.arc(0.69, 0.15, 0.1, 0, 2 * math.pi)
    cr.stroke()

    cr.arc(0.31, 0.15, 0.1, 0, 2 * math.pi)
    cr.stroke()


def draw_lilith(cr: cairo.Context):
    cr.stroke()
    cr.move_to(0.8, 0)
    cr.curve_to(-0.1, -0.3, -0.1, 1, 0.8, 0.7)
    cr.curve_to(0.3, 0.6, 0.3, 0.1, 0.8, 0)
    cr.fill()

    cr.move_to(0.5, 0.7)
    cr.line_to(0.5, 1)
    cr.move_to(0.35, 0.9)
    cr.line_to(0.65, 0.9)
    cr.stroke()


def draw_pars_fortuna(cr: cairo.Context):
    cr.arc(0.5, 0.5, 0.5, 0, 2 * math.pi)
    cr.stroke()
    cr.arc(0.5, 0.5, 0.1, 0, 2 * math.pi)
    cr.stroke()

    alpha = 2 * math.pi / 8
    for i in range(8):
        beta = alpha * i + math.pi / 8
        x2, y2 = 1, 0.5
        x2, y2 = rotate_point(0.5, 0.5, x2, y2, beta)
        x1, y1 = 0.6, 0.5
        x1, y1 = rotate_point(0.5, 0.5, x1, y1, beta)
        cr.move_to(x1, y1)
        cr.line_to(x2, y2)
        cr.stroke()

def draw_white_moon(cr: cairo.Context):

    cr.stroke()
    cr.move_to(0.2, 0)
    cr.curve_to(1.1, -0.3, 1.1, 0.9, 0.2, 0.6)
    cr.stroke()
    cr.move_to(0.2, 0.6)
    cr.curve_to(0.7, 0.5, 0.7, 0.1, 0.2, 0)
    cr.stroke()

    cr.move_to(0.5, 0.7)
    cr.line_to(0.5, 1)
    cr.move_to(0.35, 0.9)
    cr.line_to(0.65, 0.9)
    cr.stroke()


PLANET_TO_LABEL_FOO = {
    const.SUN: draw_sun, const.MOON: draw_moon,
    const.MERCURY: draw_mercury, const.VENUS: draw_venus, const.MARS: draw_mars, const.JUPITER: draw_jupiter,
    const.SATURN: draw_saturn,
    const.URANUS: draw_uranus, const.NEPTUNE: draw_neptune, const.PLUTO: draw_pluto,
    const.CHIRON: draw_chiron, const.NORTH_NODE: draw_north_node, const.SOUTH_NODE: draw_south_node,
    const.PARS_FORTUNA: draw_pars_fortuna,
    'Lilith': draw_lilith,
    'Selena': draw_white_moon
}
