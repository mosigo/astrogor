import math
from abc import abstractmethod
from datetime import datetime

import cairo

from model.sf import SoulFormula
from model.sf_flatlib import FlatlibBuilder
from view.sf_cairo import DFormula, SimpleFormulaDrawer, CirclePosition, OrbitPosition, FormulaDrawer
from view.sf_cairo_utils import save_to_pdf, CairoDrawer
from view.sf_optimization import GradientOptimization


class LayoutMaker:
    @abstractmethod
    def make_layout(self, formula: SoulFormula, width: int, height: int) -> DFormula:
        pass


class FormulaCutter:
    @abstractmethod
    def cut_formula(self, dformula: DFormula, cr: cairo.Context) -> None:
        pass

    @abstractmethod
    def get_bounds(self) -> (int, int):
        pass

    @staticmethod
    def move_points(d_formula: DFormula,
                    min_x: float, min_y: float, scale_w: float, scale_h: float) -> None:
        for planet, position in d_formula.planet_to_position.items():
            d_formula.set_planet_position(planet, CirclePosition(
                (position.x - min_x) * scale_w, (position.y - min_y) * scale_h,
                position.radius_x * scale_w, position.radius_y * scale_h))
        for center, position in d_formula.center_to_position.items():
            d_formula.set_center_position(center, CirclePosition(
                (position.x - min_x) * scale_w, (position.y - min_y) * scale_h,
                position.radius_x * scale_w, position.radius_y * scale_h))
        for orbit_num, position in d_formula.orbit_to_position.items():
            d_formula.set_orbit_position(orbit_num, OrbitPosition(
                (position.x - min_x) * scale_w, (position.y - min_y) * scale_h,
                position.w_radius_x * scale_w, position.w_radius_y * scale_h,
                position.h_radius_x * scale_w, position.h_radius_y * scale_h))
        for orbit_num, label_positions in d_formula.orbit_labels.items():
            new_label_positions = []
            for pos in label_positions:
                new_label_positions.append(
                    CirclePosition(
                        (pos.x - min_x) * scale_w,
                        (pos.y - min_y) * scale_h,
                        pos.radius_x * scale_w,
                        pos.radius_y * scale_h
                    )
                )
            d_formula.orbit_labels[orbit_num] = new_label_positions


class CircleFormulaCutter(FormulaCutter):

    def __init__(self, radius: float, padding: float = 0.15) -> None:
        self.padding = padding
        self.radius = radius

    def cut_formula(self, dformula: DFormula, cr: cairo.Context) -> None:
        x, y, r = self.__get_min_circle(dformula, cr)
        r *= 1 + self.padding
        print(x, y, r)
        min_x, min_y = x - r, y - r
        print(min_x, min_y, r)
        min_x, min_y = cr.user_to_device(min_x, min_y)
        r, _ = cr.user_to_device_distance(r, 0)
        print(min_x, min_y, r)
        scale = self.radius / r
        self.move_points(dformula, min_x, min_y, scale, scale)

    def get_bounds(self) -> (int, int):
        return self.radius * 2, self.radius * 2

    @staticmethod
    def __get_circle(x1: float, y1: float, r1: float,
                     x2: float, y2: float, r2: float,
                     x3: float, y3: float, r3: float) -> (float, float, float):
        dd = 2 * (x3 * (y1 - y2) + x1 * (y2 - y3) + x2 * (y3 - y1))
        if dd == 0:
            return None
        x = ((x3 ** 2 + y3 ** 2) * (y1 - y2) + (x1 ** 2 + y1 ** 2) * (y2 - y3) + (x2 ** 2 + y2 ** 2) * (y3 - y1)) / dd
        y = ((x3 ** 2 + y3 ** 2) * (x2 - x1) + (x1 ** 2 + y1 ** 2) * (x3 - x2) + (x2 ** 2 + y2 ** 2) * (x1 - x3)) / dd
        r = math.sqrt((x3 - x) ** 2 + (y3 - y) ** 2) + r3
        return x, y, r


    def __get_min_circle(self, d_formula: DFormula, cr: cairo.Context):
        avg_x, avg_y = 0, 0
        circles: [CirclePosition] = [a[1] for a in d_formula.planet_to_position.items()] + \
                                    [a[1] for a in d_formula.center_to_position.items()]
        for position in circles:
            x, y = position.get_center_user(cr)
            avg_x += x
            avg_y += y
        avg_x, avg_y = avg_x / len(circles), avg_y / len(circles)
        avg_r = 0
        for position in circles:
            x, y = position.get_center_user(cr)
            r = position.get_radius_user(cr)
            d = r + math.sqrt((avg_x - x) ** 2 + (avg_y - y) ** 2)
            avg_r = max(avg_r, d)

        return avg_x, avg_y, avg_r

    def __get_min_circle_by_rectangle(self, d_formula: DFormula, cr: cairo.Context):
        min_x, min_y = 1, 1
        max_x, max_y = 0, 0
        circles: [CirclePosition] = [a[1] for a in d_formula.planet_to_position.items()] + \
                                    [a[1] for a in d_formula.center_to_position.items()]
        for position in circles:
            r = position.get_radius_user(cr)
            x, y = position.get_center_user(cr)
            min_x = min(min_x, x - r)
            min_y = min(min_y, y - r)
            max_x = max(max_x, x + r)
            max_y = max(max_y, y + r)
        x, y = (min_x + max_x) / 2, (min_y + max_y) / 2
        r = math.sqrt((min_x - x) ** 2 + (min_y - y) ** 2)
        return x, y, r

    def __get_min_circle3(self, d_formula: DFormula, cr: cairo.Context):
        circles: [CirclePosition] = [a[1] for a in d_formula.planet_to_position.items()] + \
                                    [a[1] for a in d_formula.center_to_position.items()]
        max_i, max_j, max_r = 0, 0, 0
        for i in range(len(circles)):
            position_i = circles[i]
            xi, yi = position_i.get_center_user(cr)
            ri = position_i.get_radius_user(cr)
            for j in range(i + 1, len(circles)):
                position_j = circles[j]
                xj, yj = position_j.get_center_user(cr)
                if xi == xj and yi == yj:
                    continue
                rj = position_j.get_radius_user(cr)
                d = math.sqrt((xi - xj) ** 2 + (yi - yj) ** 2)
                l = d + ri + rj
                if max_r < l:
                    max_r = l
                    max_i = i
                    max_j = j
        position_i = circles[max_i]
        position_j = circles[max_j]
        xi, yi = position_i.get_center_user(cr)
        ri = position_i.get_radius_user(cr)
        xj, yj = position_j.get_center_user(cr)
        rj = position_j.get_radius_user(cr)
        d = math.sqrt((xi - xj) ** 2 + (yi - yj) ** 2)
        li, lj = d + ri, d + rj
        x1, y1 = (xi - xj) * (li / d) + xj, (yi - yj) * (li / d) + yj
        x2, y2 = (xj - xi) * (lj / d) + xi, (yj - yi) * (lj / d) + yi

        x, y = (x1 + x2) / 2, (y1 + y2) / 2
        r = (d + ri + rj) / 2

        for position in circles:
            x3, y3 = position.get_center_user(cr)
            r3 = position.get_radius_user(cr)
            d3 = math.sqrt((x - x3) ** 2 + (y - y3) ** 2)
            if d3 + r3 > r:
                dd = 2 * (x3 * (yi - yj) + xi * (yj - y3) + xj * (y3 - yi))
                if dd == 0:
                    continue
                circle = self.__get_circle(xi, yi, ri, xj, yj, rj, x3, y3, r3)
                if circle:
                    x, y, r = circle
                # x = ((x3 ** 2 + y3 ** 2) * (yi - yj) + (xi ** 2 + yi ** 2) * (yj - y3) + (xj ** 2 + yj ** 2) * (y3 - yi)) / dd
                # y = ((x3 ** 2 + y3 ** 2) * (xj - xi) + (xi ** 2 + yi ** 2) * (x3 - xj) + (xj ** 2 + yj ** 2) * (xi - x3)) / dd
                # r = math.sqrt((x3 - x) ** 2 + (y3 - y) ** 2) + r3

        return x, y, r

    def __get_min_circle2(self, d_formula: DFormula, cr: cairo.Context):
        circles: [CirclePosition] = [a[1] for a in d_formula.planet_to_position.items()] + \
                                    [a[1] for a in d_formula.center_to_position.items()]
        max_i, max_j, max_r = 0, 0, 0
        for i in range(len(circles)):
            position_i = circles[i]
            xi, yi = position_i.get_center_user(cr)
            ri = position_i.get_radius_user(cr)
            for j in range(i + 1, len(circles)):
                position_j = circles[j]
                xj, yj = position_j.get_center_user(cr)
                if xi == xj and yi == yj:
                    continue
                rj = position_j.get_radius_user(cr)
                d = math.sqrt((xi - xj) ** 2 + (yi - yj) ** 2)
                l = d + ri + rj
                if max_r < l:
                    max_r = l
                    max_i = i
                    max_j = j
        position_i = circles[max_i]
        position_j = circles[max_j]
        xi, yi = position_i.get_center_user(cr)
        ri = position_i.get_radius_user(cr)
        xj, yj = position_j.get_center_user(cr)
        rj = position_j.get_radius_user(cr)
        d = math.sqrt((xi - xj) ** 2 + (yi - yj) ** 2)
        li, lj = d + ri, d + rj
        x1, y1 = (xi - xj) * (li / d) + xj, (yi - yj) * (li / d) + yj
        x2, y2 = (xj - xi) * (lj / d) + xi, (yj - yi) * (lj / d) + yi

        x, y = (x1 + x2) / 2, (y1 + y2) / 2
        r = (d + ri + rj) / 2
        return x, y, r

    def __get_min_circle1(self, d_formula: DFormula, cr: cairo.Context):
        circles: [CirclePosition] = [a[1] for a in d_formula.planet_to_position.items()] + \
                                    [a[1] for a in d_formula.center_to_position.items()]
        min_x, min_y, min_r = 1, 1, 1
        for i in range(len(circles)):
            position_i = circles[i]
            xi, yi = position_i.get_center_user(cr)
            ri = position_i.get_radius_user(cr)
            for j in range(i + 1, len(circles)):
                position_j = circles[j]
                xj, yj = position_j.get_center_user(cr)
                if xi == xj and yi == yj:
                    continue
                rj = position_j.get_radius_user(cr)
                d = math.sqrt((xi - xj) ** 2 + (yi - yj) ** 2)
                li, lj = d + ri, d + rj
                x1, y1 = (xi - xj) * (li/d) + xj, (yi - yj) * (li/d) + yj
                x2, y2 = (xj - xi) * (lj/d) + xi, (yj - yi) * (lj/d) + yi

                x, y = (x1 + x2) / 2, (y1 + y2) / 2
                r = (d + ri + rj) / 2
                # print('xyr', xi, yi, ri, xj, yj, rj, x, y, r)

                print(i, j)
                if self.__has_all_points(circles, cr, x, y, r):
                    print('min', i, j)
                    if min_r > r:
                        min_x, min_y, min_r = x, y, r
        return min_x, min_y, min_r

    @staticmethod
    def __has_all_points(circles: [CirclePosition], cr: cairo.Context, x, y, r):
        for position in circles:
            xi, yi = position.get_center_user(cr)
            ri = position.get_radius_user(cr)

            d = math.sqrt((x - xi) ** 2 + (y - yi) ** 2)
            if d + ri - r > 0.001:
                print(x, y, r)
                print(xi, yi, ri)
                print(d)
                print()
                return False
            # if 0 < d + ri - r < 0.0001:
            #     return False
        return True


class RectangleFormulaCutter(FormulaCutter):

    def get_bounds(self) -> (int, int):
        return self.width, self.height

    def __init__(self, width: int, height: int) -> None:
        self.height = height
        self.width = width

    def cut_formula(self, d_formula: DFormula, cr: cairo.Context) -> None:
        min_x, min_y, max_x, max_y = \
            self.__get_bounds(d_formula, cr, length_ratio=self.width / self.height)
        min_x, min_y = cr.user_to_device(min_x, min_y)
        max_x, max_y = cr.user_to_device(max_x, max_y)
        scale_w, scale_h = self.width / (max_x - min_x), self.height / (max_y - min_y)
        self.move_points(d_formula, min_x, min_y, scale_w, scale_h)

    @staticmethod
    def __get_bounds(d_formula, cr: cairo.Context, length_ratio=1.0, space_ratio=0.05):
        min_x, min_y = 1, 1
        max_x, max_y = 0, 0
        circles: [CirclePosition] = [a[1] for a in d_formula.planet_to_position.items()] + \
                                    [a[1] for a in d_formula.center_to_position.items()]
        for position in circles:
            r = position.get_radius_user(cr)
            x, y = position.get_center_user(cr)
            min_x = min(min_x, x - r)
            min_y = min(min_y, y - r)
            max_x = max(max_x, x + r)
            max_y = max(max_y, y + r)
        if max_x - min_x > (max_y - min_y) * length_ratio:
            diff = ((max_x - min_x) - (max_y - min_y) * length_ratio) / 2
            min_y -= diff
            max_y += diff
        else:
            diff = ((max_y - min_y) * length_ratio - (max_x - min_x)) / 2
            min_x -= diff
            max_x += diff
        space = (max_x - min_x) * space_ratio
        min_x, min_y = min_x - space, min_y - space
        max_x, max_y = max_x + space, max_y + space

        return min_x, min_y, max_x, max_y


class DefaultLayoutMaker(LayoutMaker):

    def __init__(self, f_cutter: FormulaCutter) -> None:
        self.cutter = f_cutter

    def make_layout(self, formula: SoulFormula, width: int, height: int) -> DFormula:
        width, height = self.cutter.get_bounds()
        min_dim = min(int(width), int(height))
        surface_png = cairo.ImageSurface(cairo.FORMAT_ARGB32, min_dim, min_dim)
        ctx_png = cairo.Context(surface_png)
        ctx_png.scale(min_dim, min_dim)
        d_formula = DFormula(formula)
        self.__draw_formula(d_formula, ctx_png)
        self.cutter.cut_formula(d_formula, ctx_png)
        return d_formula

    def __get_center_size(self, center):
        return math.ceil((len(center) + 1) / 2)

    def __draw_center(self, cr: cairo.Context, d_formula: DFormula, center: [str]):
        x, y = cr.user_to_device(0.5, 0.5)
        rx, ry = cr.user_to_device_distance(0.45, 0)
        d_formula.set_center_position(tuple(center), CirclePosition(x, y, rx, ry))

        n = len(center)
        if n == 1:
            x, y = 0.5, 0.5
            radius2 = 0.3
            cr.save()
            cr.translate(x - radius2, y - radius2)
            cr.scale(2 * radius2, 2 * radius2)
            self.__draw_planet(cr, d_formula, center[0])
            cr.restore()
            return

        alpha = 2 * math.pi / n
        radius = (0.5 * math.sin(alpha / 2)) / (1.5 + math.sin(alpha / 2))
        inner_radius = 0.45 - radius
        for i in range(1, n + 1):
            y = inner_radius * math.cos(i * alpha + math.pi / 2) + 0.5
            x = inner_radius * math.sin(i * alpha + math.pi / 2) + 0.5
            radius2 = radius * inner_radius / (0.5 - radius)

            cr.save()
            cr.translate(x - radius2, y - radius2)
            cr.scale(2 * radius2, 2 * radius2)
            self.__draw_planet(cr, d_formula, center[i - 1])
            cr.restore()

    def __draw_planet(self, cr: cairo.Context, d_formula: DFormula, planet: str):
        x, y = cr.user_to_device(0.5, 0.5)
        rx, ry = cr.user_to_device_distance(0.5, 0)
        d_formula.set_planet_position(planet, CirclePosition(x, y, rx, ry))

    def __draw_orbit(self, cr: cairo.Context, x: float, y: float, width: float, height: float,
                     orbit_num: int, planets: [str], d_formula: DFormula):
        cr.save()

        cr.translate(x, y)
        cr.scale(width / 2.0, height / 2.0)

        x, y = cr.user_to_device(0, 0)
        rx1, ry1 = cr.user_to_device_distance(1, 0)
        rx2, ry2 = cr.user_to_device_distance(0, 1)
        d_formula.set_orbit_position(orbit_num, OrbitPosition(x, y, rx1, ry1, rx2, ry2))

        planets.sort(key=lambda p: 10 - len(d_formula.formula.reverse_links.get(p, [])))
        planets.sort(key=lambda p: d_formula.planet_to_position[d_formula.formula.links[p]].y)

        # j = 0
        # for p in planets:
        #     _, py = d_formula.get_planet_center_user(d_formula.formula.links[p], cr)
        #     if py > 0:
        #         break
        #     j += 1
        #
        # cell1 = 0.8 / j if j > 0 else 0
        # cell2 = 0.8 / (len(planets) - j) if j < len(planets) else 0
        cell = 1.4 / len(planets)
        for i in range(len(planets)):
            planet = planets[i]
            to_planet = d_formula.formula.links[planet]
            to_planet_x, to_planet_y = d_formula.get_planet_center_user(to_planet, cr)
            to_planet_r = d_formula.get_planet_radius_user(to_planet, cr)

            # if i < j:
            #     n_y = -0.9 + cell1 * i
            # else:
            #     n_y = 0.1 + cell2 * (i - j)

            n_y = -0.3 + cell * i
            n_x = math.sqrt(1 - n_y ** 2)
            if to_planet_x < 0:
                n_x = -n_x
            px, py = cr.user_to_device(n_x, n_y)
            # rx, ry = cr.user_to_device_distance(to_planet_r * 0.88, 0)
            k = 0.88 if orbit_num == 1 else 1
            rx, ry = cr.user_to_device_distance(to_planet_r * k, 0)
            d_formula.set_planet_position(planet, CirclePosition(px, py, rx, ry))

        cr.restore()

    def __draw_orbit_labels(self, d_formula, cr):
        i = 0
        alpha = 0
        step_in_gradus = 10
        cr.save()
        success = True
        while i < 360 / step_in_gradus:
            orbit_num_to_positions = {}
            alpha += math.pi * step_in_gradus / 180
            for orbit_num, orbit_pos in d_formula.orbit_to_position.items():
                cr.save()

                x, y = orbit_pos.get_center_user(cr)
                width = orbit_pos.get_w_radius_user(cr)
                height = orbit_pos.get_h_radius_user(cr)

                cr.translate(x, y)
                cr.scale(width, height)

                r0 = 0.1
                x1, y1 = 0, -1
                x2, y2 = math.sqrt(3) / 2, 1 / 2
                x3, y3 = -math.sqrt(3) / 2, 1 / 2

                x1, y1 = math.cos(alpha) * x1 - math.sin(alpha) * y1, math.sin(alpha) * x1 + math.cos(alpha) * y1
                x2, y2 = math.cos(alpha) * x2 - math.sin(alpha) * y2, math.sin(alpha) * x2 + math.cos(alpha) * y2
                x3, y3 = math.cos(alpha) * x3 - math.sin(alpha) * y3, math.sin(alpha) * x3 + math.cos(alpha) * y3

                for planet in d_formula.formula.orbits[orbit_num]:
                    pos = d_formula.get_planet_position(planet)
                    x, y = pos.get_center_user(cr)
                    r = pos.get_radius_user(cr)
                    r0 = r / 1.2
                    distance1 = math.sqrt((x1 - x) ** 2 + (y1 - y) ** 2) - r0 - r
                    distance2 = math.sqrt((x2 - x) ** 2 + (y2 - y) ** 2) - r0 - r
                    distance3 = math.sqrt((x3 - x) ** 2 + (y3 - y) ** 2) - r0 - r
                    if distance1 < 0 or distance2 < 0 or distance3 < 0:
                        success = False
                        break

                x1d, y1d = cr.user_to_device(x1, y1)
                x2d, y2d = cr.user_to_device(x2, y2)
                x3d, y3d = cr.user_to_device(x3, y3)
                rd, _ = cr.user_to_device_distance(r0, 0)

                orbit_num_to_positions[orbit_num] = [
                    CirclePosition(x1d, y1d, rd, 0),
                    CirclePosition(x2d, y2d, rd, 0),
                    CirclePosition(x3d, y3d, rd, 0)
                ]

                cr.restore()
                if not success:
                    break
            if success:
                # print('Положение лейблов для орбит найдены!')
                for orbit_num, positions in orbit_num_to_positions.items():
                    for pos in positions:
                        d_formula.add_orbit_label(orbit_num, pos)
                cr.restore()
                return
            else:
                # print(f'Положение лейблов для орбит не найдены, запускаю итерацию {i + 1}')
                success = True
                i += 1

    def __draw_formula(self, d_formula, cr):
        centers_to_draw = list(d_formula.formula.center)
        centers_to_draw.sort(key=lambda c: sum([len(d_formula.formula.reverse_links[a]) for a in c]), reverse=True)
        centers_to_draw.sort(key=lambda c: len(c), reverse=True)
        center_height = sum([self.__get_center_size(a) for a in centers_to_draw])
        cell = 1 / center_height

        orbit_width = cell * 1.5
        orbit_scale = 1 / (1 + orbit_width * (len(d_formula.formula.orbits) + 1))
        cr.scale(orbit_scale, orbit_scale)
        cr.translate(0.5 / orbit_scale - 0.5, 0.5 / orbit_scale - 0.5)

        for center in centers_to_draw:
            a = cell * self.__get_center_size(center)
            x = (1 - a) / 2
            cr.translate(x, 0)
            cr.scale(a, a)

            self.__draw_center(cr, d_formula, center)

            cr.scale(1 / a, 1 / a)
            cr.translate(0 - x, a)

        cr.translate(0, -1)

        for orbit_num, planets in d_formula.formula.orbits.items():
            # cur_orbit_width = orbit_width * orbit_num * 0.96 ** orbit_num
            cur_orbit_width = orbit_width * orbit_num
            orbit1_width = self.__get_center_size(centers_to_draw[0]) * cell * 1 + cur_orbit_width
            orbit1_height = 1 + cur_orbit_width

            self.__draw_orbit(cr, 0.5, 0.5, orbit1_width, orbit1_height, orbit_num, planets, d_formula)

        optimization = GradientOptimization()
        optimization.optimize(d_formula)

        self.__draw_orbit_labels(d_formula, cr)


class CairoFormulaDrawer(CairoDrawer):

    def __init__(self, formula_to_draw: DFormula, f_drawer: FormulaDrawer) -> None:
        self.f_drawer = f_drawer
        self.formula_to_draw = formula_to_draw

    def draw(self, cr: cairo.Context):
        self.f_drawer.draw_formula(self.formula_to_draw, cr)


def save_formula_to_pdf(out_path, out_width, out_height, formula_to_draw: DFormula, drawer: FormulaDrawer):

    save_to_pdf(out_path, out_width, out_height, CairoFormulaDrawer(formula_to_draw, drawer))

    # cr.set_source_rgb(0,1,0)
    # cr.set_line_width(0.01)
    # cr.stroke()
    # cr.arc(0.5, 0.5, 0.5, 0, 2 * math.pi)
    # cr.stroke()


if __name__ == '__main__':
    w, h = 97, 128
    # w, h = 200, 200
    dir = '/Users/mosigo/Yandex.Disk.localized/Documents/PycharmProjects/Astrogor/pic'

    builder = FlatlibBuilder()
    # layout_maker = DefaultLayoutMaker(RectangleFormulaCutter(w, h))
    layout_maker = DefaultLayoutMaker(CircleFormulaCutter(w/2))
    drawer = SimpleFormulaDrawer()

    # for formula_date in ['1753-04-18 12:02', '1986-07-14 12:02', '2016-12-30 12:02', '1901-06-07 12:02',
    #                      '1939-01-28 12:02', '1821-08-13 12:02', '1956-05-20 12:02', '1987-12-04 12:02',
    #                      '1987-12-24 12:02', '1987-01-10 12:02', '1992-03-19 12:02', '1990-12-13 12:02',
    #                      '1993-12-29 12:02', '1996-12-17 12:02', '1993-09-08 12:02', '1940-09-23 07:45']:
    # for formula_date in ['2022-01-10 12:02']:
    for formula_date in ['1955-02-24 12:00 -08:00']:
    # for formula_date in ['1987-01-10 10:00']:
        # for formula_date in ['2024-02-16 20:02']:
        # for formula_date in ['1970-10-25 09:15', '1970-10-17 16:43', '1955-10-19 01:07',
        #                      '1955-10-16 14:23', '1940-09-23 07:45', '1970-10-19 22:58']:
        formula = builder.build_formula(datetime.strptime(formula_date, '%Y-%m-%d %H:%M %z'))
        print(formula)
        print(formula.additional_objects)

        d_formula = layout_maker.make_layout(formula, w, h)
        print(d_formula.planet_to_position)
        print(d_formula.center_to_position)
        print(d_formula.orbit_to_position)

        save_formula_to_pdf(f"{dir}/{formula_date[:10]}_new2.pdf", w, h, d_formula, drawer)
