import math
from datetime import datetime
from typing import List

from model.sf import SoulFormula
from model.sf_flatlib import FlatlibBuilder
from view.sf_cairo import DFormula, SimpleFormulaDrawer, CirclePosition, OrbitPosition
from view.sf_geometry import rotate_point
from view.sf_layout import LayoutMaker, save_formula_to_pdf, FormulaCutter


class CircleCoordinates:
    # координаты центра окружности
    x: float
    y: float

    # радиус окружности
    r: float

    def __init__(self, x=0.0, y=0.0, r=0.0) -> None:
        self.x = x
        self.y = y
        self.r = r


class CFormula:
    # формула души, которую рисуем
    soul_formula: SoulFormula

    # список центров в порядке «значимости»
    _centers: [[str]]

    # координаты центров для каждого центра
    _center_coordinates: [CircleCoordinates]

    # координаты центра картинки; это будет центр и для окружности, описывающей все центры формулы, и для орбит
    _x0: float
    _y0: float

    # радиус планеты
    _planet_radius: float

    # ширина орбиты (расстояние между двумя орбитами)
    _orbit_width: float

    # радиус окружности, описывающей все центры формулы
    _center_radius: float

    # для каждой планеты, находящейся на орбите, храним угол в радианах, под которым она на ней расположена
    _planet_to_angle: {str, float}

    # коэффициенты сжатия по осям x и y, чтобы получить эллипсы вместо окружностей для орбит
    _compression_ratio_x: float
    _compression_ratio_y: float

    # положение планеты в формуле: в центре ('center') или на орбите ('orbit') и номер центра или орбиты соответственно
    _planet_in_formula: {str, (str, int)}

    def __init__(self, soul_formula: SoulFormula, planet_radius: float = 0, orbit_width: float = 0) -> None:
        self.soul_formula = soul_formula

        self.planet_radius = planet_radius
        self.orbit_width = orbit_width

        self._centers = []
        self._center_coordinates = []

        for center in self.soul_formula.center:
            self._center_coordinates.append(CircleCoordinates(0, 0, 0))

        self._x0 = 0.0
        self._y0 = 0.0

        self._compression_ratio_x = 1.0
        self._compression_ratio_y = 1.0

        self._center_radius = 0.0

        self._planet_to_angle = {}
        self._planet_in_formula = {}

        # про все планеты на орбитах сразу запоминаем, где они находятся
        for orbit_num, planets in self.soul_formula.orbits.items():
            for planet in planets:
                self._planet_in_formula[planet] = ('orbit', orbit_num)

    def set_center_circle_radius(self, r: float) -> None:
        self._center_radius = r

    def get_orbit_radius(self, orbit_num: int) -> float:
        return self._center_radius + orbit_num * self.orbit_width

    def get_orbit_coordinates(self, orbit_num: int) -> CircleCoordinates:
        r = self.get_orbit_radius(orbit_num)
        return CircleCoordinates(self._x0, self._y0, r)

    def get_center_coordinates(self, i: int) -> CircleCoordinates:
        return self._center_coordinates[i]

    def set_center_coordinates(self, center_num: int, coordinates: CircleCoordinates) -> None:
        self._center_coordinates[center_num] = coordinates

    def move_centers_coordinates(self, dx: float, dy: float) -> None:
        for coordinates in self._center_coordinates:
            coordinates.x += dx
            coordinates.y += dy

    def get_planet_coordinates(self, planet: str) -> CircleCoordinates:
        angle = self._planet_to_angle.get(planet)
        place, num = self._planet_in_formula.get(planet)
        if place == 'center':
            cc = self._center_coordinates[num]
            if len(self._centers[num]) == 1:
                return CircleCoordinates(cc.x, cc.y, self.planet_radius)
            xp, yp = cc.x + cc.r - self.planet_radius * 1.1, cc.y
            x, y = rotate_point(cc.x, cc.y, xp, yp, angle)
            return CircleCoordinates(x, y, self.planet_radius)
        elif place == 'orbit':
            orr = self.get_orbit_radius(num)
            xp, yp = self._x0 + orr, self._y0
            x, y = rotate_point(self._x0, self._y0, xp, yp, angle)
            return CircleCoordinates(x, y, self.planet_radius)
        raise ValueError(f'Неизвестное расположение планеты: {place} (обрабатываем только "center" и "orbit").')

    def set_coordinates(self, x: float, y: float) -> None:
        self._x0 = x
        self._y0 = y

    def get_coordinates(self) -> (float, float):
        return self._x0, self._y0

    def set_compression_ratio(self, kx: float, ky: float) -> None:
        self._compression_ratio_x = kx
        self._compression_ratio_y = ky

    def set_centers(self, centers: [[str]]) -> None:
        self._centers = centers

        # пересчитываем координаты планет, которые находятся в центрах
        for i in range(len(centers)):
            alpha = 2 * math.pi / len(centers[i])
            for j in range(len(centers[i])):
                planet = centers[i][j]
                self._planet_to_angle[planet] = alpha * j
                self._planet_in_formula[planet] = ('center', i)

    def get_centers(self) -> List[str]:
        return self._centers

    def set_orbit_planet_position(self, planet, alpha) -> None:
        self._planet_to_angle[planet] = alpha

    def get_planet_angle(self, planet) -> float:
        return self._planet_to_angle.get(planet)

    def set_planet_angle(self, planet, angle: float) -> None:
        self._planet_to_angle[planet] = angle


class AnglesLayoutMaker(LayoutMaker):
    planet_radius = 15
    center_padding = 3
    orbit_width = 50
    center_single_radius = 25

    def make_layout(self, formula: SoulFormula, width: int, height: int) -> DFormula:
        c_formula = CFormula(formula, AnglesLayoutMaker.planet_radius, AnglesLayoutMaker.orbit_width)

        # вычисляем расположение центров и планет внутри центров, пока без учёта орбит
        centers_width, centers_height = self._set_centers(c_formula)

        # сдвигаем центры так, чтобы они были внутри окружности
        dx = (centers_height - centers_width) / 2
        c_formula.move_centers_coordinates(dx, dy=0)

        # устанавливаем радиус окружности, которая описывает все центры
        c_formula.set_center_circle_radius(centers_height / 2)

        # вычисляем кол-во орбит и ширину, которая уйдёт на орбиты
        orbits_cnt = len(formula.orbits)
        orbits_width = AnglesLayoutMaker.center_padding + AnglesLayoutMaker.planet_radius + \
                       orbits_cnt * AnglesLayoutMaker.orbit_width

        # вычисляем координаты центра картинки
        x0 = orbits_width + centers_height / 2
        y0 = x0
        c_formula.set_coordinates(x0, y0)

        # сдвигаем координаты центров на ширину орбит
        c_formula.move_centers_coordinates(dx=orbits_width, dy=orbits_width)

        # выставляем позиции орбит и планеты на них
        self._set_orbits(c_formula)

        return convert_cformula_to_dformula(c_formula)

    @staticmethod
    def _center_power(f: SoulFormula, center: [str]):
        power = len(center)
        planets = list(center)
        i = 0
        while len(planets) > 0 and i < 10:
            i += 1
            p = planets.pop()
            for p_new in f.reverse_links.get(p, []):
                if p_new in f.center_set:
                    continue
                planets.append(p_new)
                power += 1
        return power

    def _set_centers(self, c: CFormula) -> (int, int):
        centers = c.soul_formula.center
        sorted_centers = sorted(centers, key=lambda cc: self._center_power(c.soul_formula, cc), reverse=True)
        c.set_centers(sorted_centers)
        radiuses = []
        for i in range(len(sorted_centers)):
            center = sorted_centers[i]

            # кол-во планет в текущем центре
            n = len(center)

            # строим правильный многогранник на n вершин (по числу планет в текущем центре)
            # a — сторона многогранника; вычисляется как три радиуса планеты,
            # чтобы между планетами можно было провести стрелочку длиной в радиус планеты
            a = AnglesLayoutMaker.planet_radius * 3

            # угол
            alpha = 2 * math.pi / n

            # радиус центра как радиус описанной окружности + небольшой отступ
            if n == 1:
                r = AnglesLayoutMaker.center_single_radius
            else:
                r = (a / 2) / math.sin(alpha / 2) + AnglesLayoutMaker.planet_radius + AnglesLayoutMaker.center_padding
            radiuses.append((r, n, alpha))

        # координата x всех центров как радиус максимального центра
        x = max([r[0] for r in radiuses])

        # координата y, исходно равна "отступ для орбит" + "внутренний отступ"
        y = AnglesLayoutMaker.center_padding

        # сохраняем в DFormula координаты
        for i in range(len(sorted_centers)):
            center = sorted_centers[i]
            r, n, alpha = radiuses[i]

            y += r
            # сначала сохраняем координаты центра
            c.set_center_coordinates(i, CircleCoordinates(x, y, r))

            # затем сохраняем углы каждой планеты центра
            alpha_cur = 0
            for planet in center:
                c.set_planet_angle(planet, alpha_cur)
                alpha_cur += alpha

            y += r + AnglesLayoutMaker.center_padding

        return x * 2, y

    @staticmethod
    def _set_orbits(c_formula: CFormula) -> None:
        for orbit_num in range(1, len(c_formula.soul_formula.orbits) + 1):

            planets = c_formula.soul_formula.orbits[orbit_num]
            planets = sorted(planets, key=lambda p: len(c_formula.soul_formula.reverse_links.get(p, [])), reverse=True)
            planets = sorted(planets, key=lambda p: c_formula.get_planet_coordinates(c_formula.soul_formula.links[p]).y)

            alpha_step = math.pi / (len(planets) + 1)
            alpha = -math.pi / 2 + alpha_step

            for planet in planets:
                to_planet = c_formula.soul_formula.links[planet]
                to_planet_alpha = c_formula.get_planet_angle(to_planet)
                da = 0
                if math.pi / 2 < to_planet_alpha < math.pi * 3 / 4:
                    da = math.pi
                c_formula.set_planet_angle(planet, alpha + da)
                alpha += alpha_step


def convert_cformula_to_dformula(c_formula: CFormula) -> DFormula:
    d_formula = DFormula(c_formula.soul_formula)
    centers = c_formula.get_centers()
    for i in range(len(centers)):
        center = centers[i]
        for planet in center:
            pc = c_formula.get_planet_coordinates(planet)
            d_formula.set_planet_position(planet, CirclePosition(pc.x, pc.y, pc.r, 0))
        cc = c_formula.get_center_coordinates(i)
        d_formula.set_center_position(tuple(center), CirclePosition(cc.x, cc.y, cc.r, 0))
    for orbit_num, planets in c_formula.soul_formula.orbits.items():
        for planet in planets:
            pc = c_formula.get_planet_coordinates(planet)
            d_formula.set_planet_position(planet, CirclePosition(pc.x, pc.y, pc.r, 0))
        oc = c_formula.get_orbit_coordinates(orbit_num)
        d_formula.set_orbit_position(orbit_num, OrbitPosition(oc.x, oc.y, oc.r, 0, oc.r, 0))
    return d_formula


if __name__ == '__main__':
    w, h = 1000, 1000
    dir = '/Users/mosigo/Yandex.Disk.localized/Documents/PycharmProjects/Astrogor/pic'

    builder = FlatlibBuilder()
    layout_maker = AnglesLayoutMaker()
    drawer = SimpleFormulaDrawer()

    for formula_date in ['1753-04-18 12:02 +03:00', '1986-07-14 12:02 +03:00', '2016-12-30 12:02 +03:00',
                         '1901-06-07 12:02 +03:00', '1939-01-28 12:02 +03:00', '1821-08-13 12:02 +03:00',
                         '1956-05-20 12:02 +03:00', '1987-12-04 12:02 +03:00', '1987-12-24 12:02 +03:00',
                         '1987-01-10 12:02 +05:00', '1992-03-19 12:02 +03:00', '1990-12-13 12:02 +03:00',
                         '1993-12-29 12:02 +03:00', '1996-12-17 12:02 +03:00', '1993-09-08 12:02 +03:00',
                         '1940-09-23 07:45 +03:00']:
        formula = builder.build_formula(datetime.strptime(formula_date, '%Y-%m-%d %H:%M %z'))
        print(formula)

        d_formula = layout_maker.make_layout(formula, w, h)
        print(d_formula.planet_to_position)
        print(d_formula.center_to_position)
        print(d_formula.orbit_to_position)
        print()

        save_formula_to_pdf(f"{dir}/{formula_date[:10]}_new2.pdf", w, h, d_formula, drawer)
