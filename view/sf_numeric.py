import math
import cairo

from model.sf import NUMBER_TO_PLANET
from view.planet_label import PlanetLabelDrawer


class NumericDrawer:

    def draw_soul_number(self, num: int, cr: cairo.Context):
        planet, (r, g, b) = NUMBER_TO_PLANET[num]

        cr.set_line_width(0.01)

        cr.set_source_rgba(r, g, b, 0.5)
        cr.move_to(0.5, 0)
        cr.line_to(1, 0)
        cr.line_to(1, 1)
        cr.line_to(0.5, 1)
        cr.arc(0.5, 0.5, 0.5, math.pi / 2, 3 * math.pi / 2)
        cr.fill()

        cr.set_source_rgb(0, 0, 0)
        cr.move_to(0.5, 0)
        cr.line_to(1, 0)
        cr.line_to(1, 1)
        cr.line_to(0.5, 1)
        cr.arc(0.5, 0.5, 0.5, math.pi / 2, 3 * math.pi / 2)
        cr.stroke()

        cr.set_source_rgb(1, 1, 1)
        cr.arc(0.5, 0.5, 0.3, 0, 2 * math.pi)
        cr.fill()

        drawer = PlanetLabelDrawer()

        cr.save()
        x, y = 0.5, 0.5
        r = 0.3 * 0.6
        cr.set_line_width(0.06)
        cr.set_source_rgb(0, 0, 0)
        cr.translate(x - r, y - r)
        cr.scale(2 * r, 2 * r)
        drawer.draw_planet(planet, cr)
        cr.restore()

        cr.stroke()

        cr.set_source_rgb(0, 0, 0)
        cr.move_to(0.8, 0.25)
        cr.set_font_size(0.25)
        cr.select_font_face("JetBrains Mono NL", cairo.FONT_SLANT_NORMAL,
                            cairo.FONT_WEIGHT_NORMAL)
        cr.show_text(str(num))
        cr.move_to(0.55, 0.95)
        cr.set_font_size(0.15)
        cr.show_text('душа')

    def draw_fate_number(self, num: int, cr: cairo.Context):
        planet, (r, g, b) = NUMBER_TO_PLANET[num]

        cr.set_line_width(0.01)

        cr.set_source_rgba(r, g, b, 0.5)
        cr.move_to(0.5, 0)
        cr.line_to(0, 0)
        cr.line_to(0, 1)
        cr.line_to(0.5, 1)
        cr.arc_negative(0.5, 0.5, 0.5, math.pi / 2, -math.pi / 2)
        cr.fill()

        cr.set_source_rgb(0, 0, 0)
        cr.move_to(0.5, 0)
        cr.line_to(0, 0)
        cr.line_to(0, 1)
        cr.line_to(0.5, 1)
        cr.arc_negative(0.5, 0.5, 0.5, math.pi / 2, -math.pi / 2)
        cr.stroke()

        cr.set_source_rgb(1, 1, 1)
        cr.arc(0.5, 0.5, 0.3, 0, 2 * math.pi)
        cr.fill()

        drawer = PlanetLabelDrawer()

        cr.save()
        x, y = 0.5, 0.5
        r = 0.3 * 0.6
        cr.set_line_width(0.06)
        cr.set_source_rgb(0, 0, 0)
        cr.translate(x - r, y - r)
        cr.scale(2 * r, 2 * r)
        drawer.draw_planet(planet, cr)
        cr.restore()

        cr.stroke()

        cr.set_source_rgb(0, 0, 0)
        cr.move_to(0.05, 0.25)
        cr.set_font_size(0.25)
        cr.select_font_face("JetBrains Mono NL", cairo.FONT_SLANT_NORMAL,
                            cairo.FONT_WEIGHT_NORMAL)
        cr.show_text(str(num))
        cr.move_to(0.05, 0.95)
        cr.set_font_size(0.15)
        cr.show_text('судьба')