import math
from abc import abstractmethod
from datetime import datetime
from typing import Dict

import cairo
from cairo import Context
from flatlib import const

from model.sf import SoulFormula, ORBIT_LABELS, SoulFormulaWithBorders
from model.sf_flatlib import FlatlibBuilder
from view.planet_label import PlanetLabelDrawer
from view.sf_geometry import rotate_point


class CirclePosition:

    def __init__(self, x: float, y: float, radius_x: float, radius_y: float) -> None:
        self.x = x
        self.y = y
        self.radius_x = radius_x
        self.radius_y = radius_y

    def get_center_device(self):
        return self.x, self.y

    def get_radius_device(self):
        return math.sqrt(self.radius_x ** 2 + self.radius_y ** 2)

    def get_center_user(self, cr: Context):
        x1, y1 = cr.device_to_user(self.x, self.y)
        return x1, y1

    def get_radius_user(self, cr: Context):
        x, y = cr.device_to_user_distance(self.radius_x, self.radius_y)
        return math.sqrt(x ** 2 + y ** 2)

    def __str__(self) -> str:
        return f'x={round(self.x, 1)}, y={round(self.y, 2)}, rx={round(self.radius_x, 2)}, ry={round(self.radius_y, 2)}'

    def __repr__(self) -> str:
        return self.__str__()


class OrbitPosition:

    def __init__(self, x: float, y: float,
                 w_radius_x: float, w_radius_y: float, h_radius_x: float, h_radius_y: float) -> None:
        self.x = x
        self.y = y
        self.w_radius_x = w_radius_x
        self.w_radius_y = w_radius_y
        self.h_radius_x = h_radius_x
        self.h_radius_y = h_radius_y

    def get_center_device(self):
        return self.x, self.y

    def get_center_user(self, cr: Context):
        x1, y1 = cr.device_to_user(self.x, self.y)
        return x1, y1

    def get_w_radius_device(self):
        return math.sqrt(self.w_radius_x ** 2 + self.w_radius_y ** 2)

    def get_w_radius_user(self, cr: Context):
        x, y = cr.device_to_user_distance(self.w_radius_x, self.w_radius_y)
        return math.sqrt(x ** 2 + y ** 2)

    def get_h_radius_device(self):
        return math.sqrt(self.h_radius_x ** 2 + self.h_radius_y ** 2)

    def get_h_radius_user(self, cr: Context):
        x, y = cr.device_to_user_distance(self.h_radius_x, self.h_radius_y)
        return math.sqrt(x ** 2 + y ** 2)

    def __str__(self) -> str:
        return f'x={round(self.x, 1)}, y={round(self.y, 1)}, ' \
               f'wrx={round(self.w_radius_x, 1)}, wry={round(self.w_radius_y, 1)}, ' \
               f'hrx={round(self.w_radius_x, 1)}, hry={round(self.w_radius_y, 1)}'

    def __repr__(self) -> str:
        return self.__str__()


class DFormula:
    planet_to_position: Dict[str, CirclePosition]
    center_to_position: Dict[str, CirclePosition]
    orbit_to_position: Dict[int, OrbitPosition]

    # orbit_labels: Dict[int, [CirclePosition]]

    def __init__(self, formula: SoulFormula) -> None:
        self.formula = formula

        self.planet_to_position = {}
        self.orbit_to_position = {}
        self.center_to_position = {}

        self.orbit_labels = {}

    def set_center_position(self, planets: (), position: CirclePosition) -> None:
        self.center_to_position[planets] = position

    def get_center_position(self, planets: ()) -> CirclePosition:
        return self.center_to_position.get(planets)

    def set_planet_position(self, planet: str, position: CirclePosition) -> None:
        self.planet_to_position[planet] = position

    def get_planet_position(self, planet: str) -> CirclePosition:
        return self.planet_to_position.get(planet)

    def get_planet_center_user(self, planet: str, cr: Context) -> (float, float):
        position = self.get_planet_position(planet)
        if position is None:
            return 0, 0
        x, y = position.get_center_user(cr)
        return x, y

    def get_planet_center_device(self, planet: str) -> (float, float):
        position = self.get_planet_position(planet)
        if position is None:
            return 0, 0
        x, y = position.get_center_device()
        return x, y

    def get_planet_x_user(self, planet: str, cr: Context) -> float:
        position = self.get_planet_position(planet)
        if position is None:
            return 0
        x, y = position.get_center_user(cr)
        return x

    def get_planet_y_user(self, planet: str, cr: Context) -> float:
        position = self.get_planet_position(planet)
        if position is None:
            return 0
        x, y = position.get_center_user(cr)
        return y

    def get_planet_x_device(self, planet: str) -> float:
        position = self.get_planet_position(planet)
        if position is None:
            return 0
        x, y = position.get_center_device()
        return x

    def get_planet_y_device(self, planet: str) -> float:
        position = self.get_planet_position(planet)
        if position is None:
            return 0
        x, y = position.get_center_device()
        return y

    def get_planet_radius_user(self, planet: str, cr: Context) -> float:
        position = self.get_planet_position(planet)
        if position is None:
            return 0
        return position.get_radius_user(cr)

    def get_planet_radius_device(self, planet: str) -> float:
        position = self.get_planet_position(planet)
        if position is None:
            return 0
        return position.get_radius_device()

    def set_orbit_position(self, num: int, position: OrbitPosition) -> None:
        self.orbit_to_position[num] = position

    def add_orbit_label(self, num: int, position: CirclePosition) -> None:
        positions = self.orbit_labels.get(num, [])
        if len(positions) == 0:
            self.orbit_labels[num] = positions
        positions.append(position)

    def get_orbit_position(self, num: int) -> OrbitPosition:
        return self.orbit_to_position.get(num)

    def get_orbit_center_user(self, num: int, cr: Context) -> (float, float):
        position = self.get_orbit_position(num)
        if position is None:
            return 0, 0
        x, y = position.get_center_user(cr)
        return x, y

    def get_orbit_center_device(self, num: int) -> (float, float):
        position = self.get_orbit_position(num)
        if position is None:
            return 0
        x, y = position.get_center_device()
        return x, y

    def get_orbit_x_user(self, num: int, cr: Context) -> float:
        position = self.get_orbit_position(num)
        if position is None:
            return 0
        x, y = position.get_center_user(cr)
        return x

    def get_orbit_y_user(self, num: int, cr: Context) -> float:
        position = self.get_orbit_position(num)
        if position is None:
            return 0
        x, y = position.get_center_user(cr)
        return y

    def get_orbit_x_device(self, num: int) -> float:
        position = self.get_orbit_position(num)
        if position is None:
            return 0
        x, y = position.get_center_device()
        return x

    def get_orbit_y_device(self, num: int) -> float:
        position = self.get_orbit_position(num)
        if position is None:
            return 0
        x, y = position.get_center_device()
        return y

    def get_orbit_w_radius_user(self, num: int, cr: Context) -> float:
        position = self.get_orbit_position(num)
        if position is None:
            return 0
        return position.get_w_radius_user(cr)

    def get_orbit_w_radius_device(self, num: int) -> float:
        position = self.get_orbit_position(num)
        if position is None:
            return 0
        return position.get_w_radius_device()

    def get_orbit_h_radius_user(self, num: int, cr: Context) -> float:
        position = self.get_orbit_position(num)
        if position is None:
            return 0
        return position.get_h_radius_user(cr)

    def get_orbit_h_radius_device(self, num: int) -> float:
        position = self.get_orbit_position(num)
        if position is None:
            return 0
        return position.get_h_radius_device()


class FormulaDrawer:

    @abstractmethod
    def draw_formula(self, d_formula, cr):
        pass

    @abstractmethod
    def draw_formula_duration(self, formula: SoulFormulaWithBorders, cr: cairo.Context):
        pass

    @abstractmethod
    def draw_power_points(self, formula: SoulFormula, cr: cairo.Context):
        pass


class DrawProfile:

    def __init__(self, font_text: str, font_header: str) -> None:
        self.font_text = font_text
        self.font_header = font_header


DrawProfile.DEFAULT = DrawProfile(
    font_text='Montserrat Light',
    font_header='Montserrat Medium'
)


class SimpleFormulaDrawer(FormulaDrawer):

    def __init__(self, draw_profile: DrawProfile = DrawProfile.DEFAULT) -> None:
        self.planet_label_drawer = PlanetLabelDrawer()
        self.planet_drawer = DefaultPlanetDrawer()

        self.draw_profile = draw_profile

    def draw_formula(self, d_formula: DFormula, cr: Context):

        # рисуем эллипсы орбит
        cr.set_line_width(0.002)
        # cr.set_source_rgb(0.2, 0.2, 0.2)
        cr.set_source_rgb(0.8, 0.8, 0.8)
        for orbit_num, position in d_formula.orbit_to_position.items():
            x, y = position.get_center_user(cr)
            r_w = position.get_w_radius_user(cr)
            r_h = position.get_h_radius_user(cr)

            cr.save()
            cr.translate(x, y)
            cr.scale(r_w, r_h)
            cr.arc(0.0, 0.0, 1.0, 0.0, 2.0 * math.pi)
            cr.stroke()
            cr.restore()

        # рисуем лейблы для орбит
        for orbit_num, label_positions in d_formula.orbit_labels.items():
            planet = ORBIT_LABELS[orbit_num - 1]
            for label_pos in label_positions:
                x, y = label_pos.get_center_user(cr)
                r = label_pos.get_radius_user(cr)
                cr.set_source_rgb(1, 1, 1)
                cr.set_line_width(0.002)
                cr.arc(x, y, r, 0, math.pi * 2)
                cr.fill()

                cr.save()
                cr.set_line_width(0.03)
                cr.set_source_rgb(0.8, 0.8, 0.8)
                # cr.set_source_rgb(0.3, 0.3, 0.3)
                label_radius = 0.6 * r
                cr.translate(x - label_radius, y - label_radius)
                cr.scale(2 * label_radius, 2 * label_radius)
                self.planet_label_drawer.draw_planet(planet, cr)
                cr.restore()

        # рисуем центры формулы души (без планет, только сами центры)
        for center, center_position in d_formula.center_to_position.items():
            x, y = center_position.get_center_user(cr)
            r = center_position.get_radius_user(cr)
            cr.set_line_width(0.02)
            cr.set_source_rgba(1, 0, 0, 0.5)
            cr.arc(x, y, r, 0, 2 * math.pi)
            cr.stroke()
            cr.set_source_rgb(221 / 255, 228 / 255, 1)
            cr.arc(x, y, r, 0, 2 * math.pi)
            cr.fill()

        # рисуем cтрелочки между планетами
        for planet, position in d_formula.planet_to_position.items():
            x, y = position.get_center_user(cr)
            r = position.get_radius_user(cr)

            # если планета в формуле указывает не на себя саму, то рисуем к нужной планете стрелочку
            to_planet = d_formula.formula.links[planet]
            if planet != to_planet:
                x1, y1 = d_formula.get_planet_center_user(to_planet, cr)
                r1 = d_formula.get_planet_radius_user(to_planet, cr)
                spacer = 0 if d_formula.formula.links[to_planet] != planet else math.pi / 24
                cr.set_line_cap(cairo.LINE_CAP_ROUND)
                cr.set_line_width(0.002)
                cr.set_source_rgb(0, 0, 0)
                self.draw_arrow_between_circles(cr, x, y, r, x1, y1, r1, spacer=spacer)

        # рисуем сами планеты
        for planet, position in d_formula.planet_to_position.items():
            x, y = position.get_center_user(cr)
            r = position.get_radius_user(cr)
            additional_planets = []
            for add_planet, to_planet in d_formula.formula.additional_objects.items():
                if to_planet == planet:
                    additional_planets.append((add_planet, add_planet in d_formula.formula.retro))

            self.planet_drawer.draw_planet(planet, cr, x, y, r,
                                           is_retro=planet in d_formula.formula.retro,
                                           power=d_formula.formula.planet_power[planet],
                                           is_own_orbit=planet in d_formula.formula.own_orbits,
                                           additional_planets=additional_planets)

    def draw_formula_duration(self, formula: SoulFormulaWithBorders, cr: cairo.Context):
        cr.set_line_width(0.002)
        cr.move_to(0.1, 0.56)
        cr.line_to(0.9, 0.56)
        cr.stroke()

        cr.select_font_face(self.draw_profile.font_text, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(0.12)
        cr.move_to(0.07, 0.50)
        cr.show_text('с ' + formula.from_dt.strftime("%d.%m %H:%M"))
        cr.move_to(0.10, 0.71)
        cr.show_text('до ' + formula.to_dt.strftime("%d.%m %H:%M"))
        cr.stroke()

        cr.select_font_face(self.draw_profile.font_header, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.move_to(0.14, 0.31)
        cr.set_font_size(0.085)
        cr.show_text('Время формулы')
        cr.stroke()

    def draw_power_points(self, formula: SoulFormula, cr: cairo.Context):
        private_cnt = 0
        for planet in [const.SUN, const.MOON,
                       const.MERCURY, const.VENUS, const.MARS]:
            private_cnt += formula.planet_power[planet]
        private_pcnt = min(27, private_cnt) / 27

        social_cnt = 0
        for planet in [const.JUPITER, const.SATURN]:
            social_cnt += formula.planet_power[planet]
        social_pcnt = social_cnt / 12

        transuran_cnt = 0
        for planet in [const.URANUS, const.NEPTUNE, const.PLUTO]:
            transuran_cnt += formula.planet_power[planet]
        transuran_pcnt = transuran_cnt / 18

        all_cnt = private_cnt + social_cnt + transuran_cnt
        all_pcnt = (min(27, private_cnt) + social_cnt + transuran_cnt) / (27 + 12 + 18)

        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(0.005)
        cr.move_to(0.3, 0.28)
        cr.line_to(0.3, 0.85)
        cr.stroke()
        cr.set_line_width(0.001)
        cr.set_source_rgba(0.3, 0.3, 0.3)
        cr.move_to(0.8, 0.28)
        cr.line_to(0.8, 0.85)
        cr.stroke()
        cr.move_to(0.55, 0.28)
        cr.line_to(0.55, 0.85)
        cr.stroke()
        cr.move_to(0.05, 0.71)
        cr.line_to(0.95, 0.71)
        cr.stroke()

        cr.set_source_rgba(0.5, 0.5, 0.5, 0.5)
        cr.rectangle(0.3, 0.3, 0.5 * private_pcnt, 0.12)
        cr.rectangle(0.3, 0.43, 0.5 * social_pcnt, 0.12)
        cr.rectangle(0.3, 0.56, 0.5 * transuran_pcnt, 0.12)
        cr.rectangle(0.3, 0.74, 0.5 * all_pcnt, 0.08)
        cr.fill()

        cr.set_font_size(0.065)
        cr.set_source_rgb(0, 0, 0)
        cr.select_font_face(self.draw_profile.font_text, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.move_to(0.10, 0.38)
        cr.show_text('Личн')
        cr.move_to(0.83, 0.38)
        cr.show_text(str(private_cnt))
        cr.move_to(0.14, 0.51)
        cr.show_text('Соц')
        cr.move_to(0.83, 0.51)
        cr.show_text(str(social_cnt))
        cr.move_to(0.03, 0.64)
        cr.show_text('Задумч')
        cr.move_to(0.83, 0.64)
        cr.show_text(str(transuran_cnt))
        cr.move_to(0.075, 0.80)
        cr.show_text('Всего')
        cr.move_to(0.83, 0.80)
        cr.show_text(str(all_cnt))
        cr.stroke()

        cr.select_font_face(self.draw_profile.font_header, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(0.085)
        cr.move_to(0.22, 0.22)
        cr.show_text('Сила планет')
        cr.stroke()

    def draw_arrow(self, cr, x1, y1, x2, y2, koeff=0.02):
        cr.move_to(x1, y1)
        cr.line_to(x2, y2)
        cr.stroke()

        length = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

        arrow_len = koeff / length
        cr.move_to(x2, y2)
        cr.line_to(arrow_len * math.cos(math.pi / 6) * (x1 - x2) - arrow_len * math.sin(math.pi / 6) * (y1 - y2) + x2,
                   arrow_len * math.sin(math.pi / 6) * (x1 - x2) + arrow_len * math.cos(math.pi / 6) * (y1 - y2) + y2)
        cr.stroke()
        cr.move_to(x2, y2)
        cr.line_to(arrow_len * math.cos(math.pi / 6) * (x1 - x2) + arrow_len * math.sin(math.pi / 6) * (y1 - y2) + x2,
                   -arrow_len * math.sin(math.pi / 6) * (x1 - x2) + arrow_len * math.cos(math.pi / 6) * (y1 - y2) + y2)
        cr.stroke()

    def draw_arrow_between_circles(self, cr, x1, y1, r1, x2, y2, r2, koeff=0.9, arrow_koeff=0.01, spacer=0):
        x, y = x2 - x1, y2 - y1
        v_len = math.sqrt(x ** 2 + y ** 2)
        arrow_len = (v_len - r1 - r2) * koeff
        r_add = (v_len - r1 - r2 - arrow_len) / 2
        m1, n1 = (r1 + r_add) * x / v_len, (r1 + r_add) * y / v_len
        m1, n1 = m1 * math.cos(spacer) - n1 * math.sin(spacer), m1 * math.sin(spacer) + n1 * math.cos(spacer)
        a1, b1 = x1 + m1, y1 + n1
        m2, n2 = - (r2 + r_add) * x / v_len, - (r2 + r_add) * y / v_len
        m2, n2 = m2 * math.cos(spacer) + n2 * math.sin(spacer), - m2 * math.sin(spacer) + n2 * math.cos(spacer)
        a2, b2 = x2 + m2, y2 + n2
        self.draw_arrow(cr, a1, b1, a2, b2, arrow_koeff)


class PlanetDrawer:
    @abstractmethod
    def draw_planet(self, planet: str, cr: cairo.Context, x: float, y: float, r: float,
                    is_retro=False, power=None, is_own_orbit=False, additional_planets=None, is_selected=False) -> None:
        pass


class DefaultPlanetDrawer(PlanetDrawer):

    def __init__(self, draw_profile:DrawProfile = DrawProfile.DEFAULT) -> None:
        self.planet_drawer = PlanetLabelDrawer()

        self.draw_profile = draw_profile

    def draw_planet(self, planet: str, cr: cairo.Context, x: float, y: float, r: float,
                    is_retro=False, power=None, is_own_orbit=False, additional_planets=None, is_selected=False,
                    label_line_width=0.06) -> None:
        # рисуем кружочек с обводкой и белой заливкой
        cr.set_line_width(0.001)
        cr.set_source_rgb(1, 1, 1)
        if is_selected:
            cr.set_source_rgb(1, 1, 0.8)
        cr.arc(x, y, r, 0, 2 * math.pi)
        cr.fill()
        cr.set_source_rgb(0, 0, 0)
        cr.arc(x, y, r, 0, 2 * math.pi)
        cr.stroke()

        # рисуем лейбл планеты
        cr.save()
        cr.set_line_width(label_line_width)
        cr.set_source_rgb(0, 0, 0)
        if is_retro:
            cr.set_source_rgb(1, 0, 0)
        label_radius = 0.6 * r
        cr.translate(x - label_radius, y - label_radius)
        cr.scale(2 * label_radius, 2 * label_radius)
        self.planet_drawer.draw_planet(planet, cr)
        cr.restore()

        # если планета на своей орбите, то рисуем ей красную рамку
        if is_own_orbit:
            cr.set_line_width(0.007)
            cr.set_line_cap(cairo.LINE_CAP_SQUARE)
            cr.set_source_rgba(1, 0, 0, 0.5)
            alpha = 0
            space = 7 * math.pi / 180
            step = math.pi / 6
            while alpha < 2 * math.pi:
                cr.arc(x, y, r, alpha + space, alpha + step - space)
                cr.stroke()
                alpha += step

        # рисуем силу планеты в баллах
        if power is not None:
            p_x, p_y = x + r / math.sqrt(2), y - r / math.sqrt(2)
            p_r = r / 2.8

            cr.set_line_width(0.001)
            cr.move_to(p_x, p_y)
            cr.set_source_rgb(1, 1, 1)
            cr.arc(p_x, p_y, p_r, 0, 2 * math.pi)
            cr.fill()

            # cr.arc(p_x, p_y, p_r, 0, 2 * math.pi)
            # cr.stroke()

            cr.set_font_size(p_r * 2)

            cr.move_to(p_x - p_r / 2, p_y + p_r / 2)
            cr.set_source_rgb(0, 0, 0)
            cr.select_font_face(self.draw_profile.font_text, cairo.FONT_SLANT_NORMAL,
                                cairo.FONT_WEIGHT_NORMAL)
            cr.show_text(str(power))

        # рисуем дополнительные "планеты": узел кармы, Хирон, белая и чёрная луна...
        if additional_planets:
            for i in range(len(additional_planets)):
                x1 = x
                y1 = y - r
                r1 = r / 3
                alpha = 2 * math.asin(r1 / r)
                x1, y1 = rotate_point(x, y, x1, y1, -alpha * i)
                rl = r1 * 0.8
                planet, planet_is_retro = additional_planets[i]
                cr.set_source_rgb(1, 1, 0.8)
                cr.arc(x1, y1, r1, 0, 2 * math.pi)
                cr.fill()
                cr.set_source_rgb(0, 0, 0)
                # cr.arc(x1, y1, r1, 0, 2 * math.pi)
                # cr.stroke()

                cr.save()
                cr.set_line_width(0.09)
                if planet_is_retro:
                    cr.set_source_rgb(1, 0, 0)
                cr.translate(x1 - rl, y1 - rl)
                cr.scale(2 * rl, 2 * rl)
                self.planet_drawer.draw_planet(planet, cr)
                cr.restore()


if __name__ == '__main__':
    builder = FlatlibBuilder()
    formula_date = '1956-05-20 12:02'
    formula = builder.build_formula(datetime.strptime(formula_date, '%Y-%m-%d %H:%M'))
    print(formula)

    width, height = 500, 500

    dir = '/Users/mosigo/Yandex.Disk.localized/Documents/PycharmProjects/Astrogor/pic'
    surface_pdf = cairo.PDFSurface(f"{dir}/{formula_date[:10]}_new.pdf", width, height)
    surface_pdf.set_fallback_resolution(500, 500)
    cr = cairo.Context(surface_pdf)

    cr.scale(width, height)

    d_formula = DFormula(formula)

    d_formula.set_center_position(
        (const.MOON, const.VENUS),
        CirclePosition(79.16, 208.52, 109.94, 0)
    )

    d_formula.set_center_position(
        (const.MERCURY),
        CirclePosition(79.16, 373.43, 54.97, 0)
    )

    d_formula.set_planet_position(
        const.MOON,
        CirclePosition(79.16, 149.15, 39.58, 0)
    )

    d_formula.set_planet_position(
        const.VENUS,
        CirclePosition(79.16, 267.88, 39.58, 0)
    )

    d_formula.set_planet_position(
        const.MERCURY,
        CirclePosition(79.16, 373.43, 32.98, 0)
    )

    d_formula.set_planet_position(
        const.URANUS,
        CirclePosition(236.47, 121.08, 27.48, 0)
    )

    d_formula.set_planet_position(
        const.SUN,
        CirclePosition(267.77, 214.71, 27.48, 0)
    )

    d_formula.set_planet_position(
        const.NEPTUNE,
        CirclePosition(267.08, 316.51, 27.48, 0)
    )

    d_formula.set_planet_position(
        const.MARS,
        CirclePosition(327.06, 121.08, 27.48, 0)
    )

    d_formula.set_planet_position(
        const.PLUTO,
        CirclePosition(349.15, 201.80, 27.48, 0)
    )

    d_formula.set_planet_position(
        const.JUPITER,
        CirclePosition(353.98, 267.84, 27.48, 0)
    )

    d_formula.set_planet_position(
        const.SATURN,
        CirclePosition(432.94, 205.77, 27.48, 0)
    )

    d_formula.set_orbit_position(
        1,
        OrbitPosition(79.16, 263.49, 192.39, 0, 247.36, 0)
    )

    d_formula.set_orbit_position(
        2,
        OrbitPosition(79.16, 263.49, 274.85, 0, 329.82, 0)
    )

    d_formula.set_orbit_position(
        3,
        OrbitPosition(79.16, 263.49, 357.30, 0, 412.27, 0)
    )

    d_formula.add_orbit_label(1, CirclePosition(79.16, 263.49 - 247.36, 27.48 / 2, 0))

    drawer = SimpleFormulaDrawer()
    drawer.draw_formula(d_formula, cr)
