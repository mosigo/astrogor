import random

import cairo
import math


def ellipse(cr0: cairo.Context) -> None:
    cr0.set_line_width(0.001)

    x0, y0 = 0.5, 0.5
    rw, rh = 0.5, 0.3
    rw_rh = rw / rh

    cr0.arc(x0, y0, rw, 0, 2 * math.pi)
    cr0.stroke()
    cr0.arc(x0, y0, rh, 0, 2 * math.pi)
    cr0.stroke()

    alpha = 0
    while alpha <= 2 * math.pi:
        x1 = x0 + rw * math.cos(math.atan(rw_rh * math.tan(alpha)))
        y1 = y0 + rh * math.sin(math.atan(rw_rh * math.tan(alpha)))
        cr0.arc(x1, y1, 0.005, 0, 2 * math.pi)
        cr0.fill()
        alpha += math.pi / 18

    cr0.stroke()


def get_alpha(x0, y0, r0, x1, y1):
    a = math.sqrt((x0 + r0 - x1) ** 2 + (y0 - y1) ** 2)
    k = 1 if y1 > y0 else -1
    return 2 * k * math.asin(a / 2 / r0)


def optimization_function(cr0: cairo.Context):
    cr0.set_line_width(0.001)

    x0, y0 = 0.5, 0.5
    r0 = 0.4

    cr0.arc(x0, y0, r0, 0, 2 * math.pi)
    cr0.stroke()

    alpha1 = 200 * math.pi / 180
    alpha2 = 10 * math.pi / 180

    x1, y1 = x0 + r0 * math.cos(alpha1), y0 + r0 * math.sin(alpha1)
    x2, y2 = x0 + r0 * math.cos(alpha2), y0 + r0 * math.sin(alpha2)
    r = 0.01

    cr0.arc(x1, y1, r, 0, 2 * math.pi)
    cr0.fill()

    cr0.arc(x2, y2, r, 0, 2 * math.pi)
    cr0.fill()

    cr0.set_font_size(0.01)

    beta1 = get_alpha(x0, y0, r0, x1, y1)
    beta2 = get_alpha(x0, y0, r0, x2, y2)

    cr0.move_to(x1 + 0.01, y1 + 0.01)
    cr0.show_text(str(beta1 * 180 / math.pi))
    cr0.stroke()

    cr0.move_to(x2 + 0.01, y2 + 0.01)
    cr0.show_text(str(beta2 * 180 / math.pi))
    cr0.stroke()


def favicon(cr0: cairo.Context):
    cr0.set_source_rgb(0, 0, 0.8)
    x0, y0 = 0.5, 0.5
    r0 = 0.5

    cr0.set_line_width(0.005)
    cr0.arc(x0, y0, r0, 0, 2 * math.pi)
    cr0.stroke()

    angles = []
    while len(angles) < 100:
        angles.append(random.random() * 360)

    for angle in angles:
        alpha1 = angle * math.pi / 180

        x, y = x0 + r0 * math.cos(alpha1), y0 + r0 * math.sin(alpha1)
        r = 0.01

        cr0.arc(x, y, r, 0, 2 * math.pi)
        cr0.fill()

        i = int(random.random() * len(angles))
        alpha2 = angles[i]
        x2, y2 = x0 + r0 * math.cos(alpha2), y0 + r0 * math.sin(alpha2)
        cr0.set_line_width(0.002)
        cr0.move_to(x, y)
        cr0.line_to(x2, y2)
        cr0.stroke()


if __name__ == '__main__':
    # surface = cairo.PDFSurface(f"pic/ellipse.pdf", 300, 300)
    # cr = cairo.Context(surface)
    # cr.scale(300, 300)
    #
    # # ellipse(cr)
    # optimization_function(cr)
    #
    # surface.finish()

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 300, 300)
    cr = cairo.Context(surface)
    cr.scale(300, 300)

    # ellipse(cr)
    # optimization_function(cr)
    favicon(cr)

    surface.write_to_png(f"pic/ellipse.png")

    surface.finish()
