import math

from math import pi

import cairo
from flatlib import const


class SignLabelDrawer:
    def draw_sign(self, sign, cr):
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        # cr.rectangle(0, 0, 1, 1)
        # cr.stroke()
        SIGN_TO_LABEL_FOO[sign](cr)


def draw_aries(cr: cairo.Context):
    cr.move_to(0.51, 1)
    cr.line_to(0.51, 0.3)
    cr.curve_to(0.51, 0, 1, 0, 1, 0.3)
    cr.curve_to(1, 0.5, 0.75, 0.5, 0.75, 0.4)

    cr.move_to(0.49, 1)
    cr.line_to(0.49, 0.3)
    cr.curve_to(0.49, 0, 0, 0, 0, 0.3)
    cr.curve_to(0, 0.5, 0.25, 0.5, 0.25, 0.4)

    cr.stroke()


def draw_taurus(cr):
    cr.arc(0.5, 0.7, 0.4, 0, 2 * pi)
    cr.stroke()
    cr.arc(0.5, 0, 0.32, 0, pi)
    cr.stroke()


def draw_gemini(cr: cairo.Context):
    cr.move_to(0.25, 0.08)
    cr.line_to(0.25, 0.92)
    cr.move_to(0.75, 0.08)
    cr.line_to(0.75, 0.92)
    cr.stroke()
    cr.arc(0.5, -1.9, 2, 5 * pi / 12, 7 * pi / 12)
    cr.stroke()
    cr.arc(0.5, 2.9, 2, -7 * pi / 12, -5 * pi / 12)
    cr.stroke()


def draw_cancer(cr: cairo.Context):
    cr.arc(0.25, 0.75, 0.2, 0, 2 * pi)
    cr.stroke()
    cr.arc(0.75, 0.25, 0.2, 0, 2 * pi)
    cr.stroke()

    cr.move_to(0.21, 0.95)
    cr.curve_to(0.6, 1.1, 0.9, 0.95, 1, 0.6)
    cr.stroke()

    cr.move_to(0.79, 0.05)
    cr.curve_to(0.4, -0.1, 0.1, 0.05, 0, 0.4)
    cr.stroke()


def draw_leo(cr: cairo.Context):
    cr.arc(0.26, 0.62, 0.15, 0, 2 * pi)
    cr.stroke()
    cr.move_to(0.38, 0.52)
    cr.curve_to(0.2, 0.35, 0.2, 0, 0.5, 0)
    cr.curve_to(0.8, 0, 0.8, 0.3, 0.62, 0.58)
    cr.curve_to(0.5, 0.75, 0.5, 0.9, 0.62, 0.95)
    cr.curve_to(0.75, 0.98, 0.82, 0.9, 0.8, 0.8)
    cr.stroke()


def draw_virgo(cr: cairo.Context):
    cr.move_to(0.25, 0.8)
    cr.line_to(0.25, 0.1)
    cr.stroke()

    cr.move_to(0.5, 0.8)
    cr.line_to(0.5, 0.1)
    cr.stroke()

    cr.move_to(0.25, 0.1)
    cr.curve_to(0.25, -0.05, 0, -0.05, 0, 0.1)
    cr.stroke()

    cr.move_to(0.5, 0.1)
    cr.curve_to(0.5, -0.05, 0.25, -0.05, 0.25, 0.1)
    cr.stroke()

    cr.move_to(0.75, 0.1)
    cr.curve_to(0.75, -0.05, 0.5, -0.05, 0.5, 0.1)
    cr.stroke()

    cr.move_to(0.9, 1)
    cr.curve_to(0.5, 0.5, 0.6, 0.1, 0.75, 0.1)
    cr.curve_to(0.9, 0.1, 1, 0.5, 0.6, 1)
    cr.stroke()


def draw_libra(cr: cairo.Context):
    cr.move_to(0, 1)
    cr.line_to(1, 1)
    cr.stroke()

    cr.move_to(0.3, 0.8)
    cr.line_to(0, 0.8)
    cr.stroke()

    cr.move_to(0.7, 0.8)
    cr.line_to(1, 0.8)
    cr.stroke()

    cr.move_to(0.3, 0.8)
    cr.curve_to(0, 0.5, 0, 0, 0.5, 0)
    cr.curve_to(1, 0, 1, 0.5, 0.7, 0.8)
    cr.stroke()


def draw_scorpio(cr: cairo.Context):
    cr.move_to(0.25, 0.8)
    cr.line_to(0.25, 0.1)
    cr.stroke()

    cr.move_to(0.5, 0.8)
    cr.line_to(0.5, 0.1)
    cr.stroke()

    cr.move_to(0.75, 0.8)
    cr.line_to(0.75, 0.1)
    cr.stroke()

    cr.move_to(0.25, 0.1)
    cr.curve_to(0.25, -0.05, 0, -0.05, 0, 0.1)
    cr.stroke()

    cr.move_to(0.5, 0.1)
    cr.curve_to(0.5, -0.05, 0.25, -0.05, 0.25, 0.1)
    cr.stroke()

    cr.move_to(0.75, 0.1)
    cr.curve_to(0.75, -0.05, 0.5, -0.05, 0.5, 0.1)
    cr.stroke()

    cr.move_to(0.75, 0.8)
    cr.curve_to(0.75, 1, 1, 1, 1, 0.8)
    cr.stroke()

    cr.move_to(0.95, 0.84)
    cr.line_to(1, 0.8)
    cr.line_to(1.04, 0.85)
    cr.stroke()


def draw_sagittarius(cr: cairo.Context):
    cr.move_to(0, 1)
    cr.line_to(1, 0)
    cr.stroke()

    cr.move_to(0.8, 0)
    cr.line_to(1, 0)
    cr.line_to(1, 0.2)
    cr.stroke()

    cr.move_to(0.25, 0.5)
    cr.line_to(0.5, 0.75)
    cr.stroke()


def draw_capricorn(cr: cairo.Context):
    cr.move_to(0.1, 0)
    cr.line_to(0.8, 0)

    cr.curve_to(0.1, 0.25, 0.1, 1, 0.5, 1)
    cr.curve_to(1, 1, 1, 0.4, 0.5, 0.4)
    cr.curve_to(0.5, 0.4, 0.2, 0.4, 0.1, 0.65)

    cr.stroke()


def draw_aquarius(cr: cairo.Context):
    cr.move_to(0, 0.5)
    cr.line_to(0.25, 0.25)
    cr.line_to(0.5, 0.5)
    cr.line_to(0.75, 0.25)
    cr.line_to(1, 0.5)
    cr.stroke()

    cr.move_to(0, 0.75)
    cr.line_to(0.25, 0.5)
    cr.line_to(0.5, 0.75)
    cr.line_to(0.75, 0.5)
    cr.line_to(1, 0.75)
    cr.stroke()


def draw_pisces(cr: cairo.Context):
    cr.arc(-0.2, 0.5, 0.6, -1*pi/4, 1*pi/4)
    cr.stroke()
    cr.arc(1.2, 0.5, 0.6, 3*pi/4, 2 * pi - 3*pi/4)
    cr.stroke()
    cr.move_to(0.25, 0.5)
    cr.line_to(0.75, 0.5)
    cr.stroke()


# ARIES, TAURUS, GEMINI, CANCER, LEO, VIRGO, LIBRA,
#                       SCORPIO, SAGITTARIUS, CAPRICORN, AQUARIUS, PISCES
SIGN_TO_LABEL_FOO = {
    const.ARIES: draw_aries, const.TAURUS: draw_taurus,
    const.GEMINI: draw_gemini, const.CANCER: draw_cancer, const.LEO: draw_leo, const.VIRGO: draw_virgo,
    const.LIBRA: draw_libra,
    const.SCORPIO: draw_scorpio, const.SAGITTARIUS: draw_sagittarius, const.CAPRICORN: draw_capricorn,
    const.AQUARIUS: draw_aquarius, const.PISCES: draw_pisces
}
