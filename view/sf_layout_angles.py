import math
from datetime import datetime

from model.sf import SoulFormula
from model.sf_flatlib import FlatlibBuilder
from view.sf_cairo import DFormula, SimpleFormulaDrawer, CirclePosition, OrbitPosition
from view.sf_geometry import rotate_point
from view.sf_layout import LayoutMaker, save_formula_to_pdf, FormulaCutter


class AnglesLayoutMaker(LayoutMaker):
    planet_radius = 15
    center_padding = 3
    orbit_width = 50
    center_single_radius = 25

    def make_layout(self, formula: SoulFormula, width: int, height: int) -> DFormula:
        d_formula = DFormula(formula)

        # вычисляем расположение центров и планет внутри центров, пока без учёта орбит
        centers_width, centers_height = self._set_centers(d_formula)
        dx = (centers_height - centers_width) / 2

        print('centers_height', centers_height)

        # вычисляем кол-во орбит и ширину, которая уйдёт на орбиты
        orbits_cnt = len(formula.orbits)
        orbits_width = AnglesLayoutMaker.center_padding + AnglesLayoutMaker.planet_radius + \
                       orbits_cnt * AnglesLayoutMaker.orbit_width

        print('orbits_width', orbits_width)

        # сдвигаем все центры и планеты на ширину, необходимую для орбит
        FormulaCutter.move_points(d_formula, -(orbits_width + dx), -orbits_width, scale_w=1, scale_h=1)
        p = int(orbits_width + centers_height / 2)

        # выставляем позиции орбит и планеты на них
        self._set_orbits(d_formula, x0=p, y0=p, center_radius=centers_height / 2)

        return d_formula

    def _center_power(self, f: SoulFormula, center: [str]):
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

    def _set_centers(self, d: DFormula) -> (int, int):
        centers = d.formula.center
        sorted_centers = sorted(centers, key=lambda c: self._center_power(d.formula, c), reverse=True)
        radiuses = []
        for center in sorted_centers:
            # кол-во планет в текущем центре
            n = len(center)

            # строим правильный многогранник на n вершин (по числу планет в текущем центре)
            # a — сторона многогранника; вычисляется как три радиуса планеты,
            # чтобы между планетами можно было провести стрелочку длиной в диаметр планеты
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
            d.set_center_position(tuple(center), CirclePosition(x, y, r, 0))

            alpha_cur = 0
            if n == 1:
                x0, y0 = x, y
            else:
                x0, y0 = x + r - AnglesLayoutMaker.planet_radius - AnglesLayoutMaker.center_padding, y
            # затем сохраняем координаты каждой планеты центра
            for planet in center:
                x_cur, y_cur = rotate_point(x, y, x0, y0, alpha_cur)
                d.planet_to_position[planet] = \
                    CirclePosition(x_cur, y_cur, AnglesLayoutMaker.planet_radius, 0)
                alpha_cur += alpha

            y += r + AnglesLayoutMaker.center_padding

        return x * 2, y

    def _set_orbits(self, d_formula: DFormula, x0: int, y0: int, center_radius: float) -> None:
        rw, rh = center_radius + AnglesLayoutMaker.orbit_width, center_radius + AnglesLayoutMaker.orbit_width
        for orbit_num in range(1, len(d_formula.formula.orbits) + 1):

            d_formula.orbit_to_position[orbit_num] = OrbitPosition(x0, y0, rw, 0, rh, 0)

            planets = d_formula.formula.orbits[orbit_num]
            planets = sorted(planets, key=lambda p: len(d_formula.formula.reverse_links.get(p, [])), reverse=True)
            planets = sorted(planets, key=lambda p: d_formula.planet_to_position[d_formula.formula.links[p]].y)
            h = min(
                (AnglesLayoutMaker.planet_radius * 2 + AnglesLayoutMaker.center_padding * 2) * (len(planets) - 1),
                rw * 2 * 0.8
            )
            y_step = h / (len(planets) - 1) if len(planets) > 1 else h
            yp = y0 - h / 2
            for planet in planets:
                xp = math.sqrt(rw ** 2 - (yp - y0) ** 2) + x0
                d_formula.planet_to_position[planet] = \
                    CirclePosition(xp, yp, AnglesLayoutMaker.planet_radius, 0)

                yp += y_step

            rw, rh = rw + AnglesLayoutMaker.orbit_width, rh + AnglesLayoutMaker.orbit_width


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

        save_formula_to_pdf(f"{dir}/{formula_date[:10]}_new2.pdf", w, h, d_formula, drawer)
