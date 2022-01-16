import itertools
import math
import shutil
from abc import abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List

import cairo

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
    planet_radius: float

    # ширина орбиты (расстояние между двумя орбитами)
    orbit_width: float

    # насколько лейбл орбиты меньше, чем планета; если 1, то размеры равны
    orbit_label_ratio: float

    # радиус окружности, описывающей все центры формулы
    _center_radius: float

    # для каждой планеты, находящейся на орбите, храним угол в радианах, под которым она на ней расположена
    _planet_to_angle: {str, float}

    # коэффициенты сжатия по осям x и y, чтобы получить эллипсы вместо окружностей для орбит
    _compression_ratio_x: float
    _compression_ratio_y: float

    # положение планеты в формуле: в центре ('center') или на орбите ('orbit') и номер центра или орбиты соответственно
    _planet_in_formula: {str, (str, int)}

    # углы, под которыми будут располагаться лейблы орбит
    _orbit_label_angles: [float]

    def __init__(self, soul_formula: SoulFormula, planet_radius: float = 0, orbit_width: float = 0,
                 orbit_label_ratio: float = 0.8) -> None:
        self.soul_formula = soul_formula

        self.planet_radius = planet_radius
        self.orbit_width = orbit_width
        self.orbit_label_ratio = orbit_label_ratio

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

        self._orbit_label_angles = []

        # про все планеты на орбитах сразу запоминаем, где они находятся
        for orbit_num, planets in self.soul_formula.orbits.items():
            for planet in planets:
                self._planet_in_formula[planet] = ('orbit', orbit_num)

    def copy(self):
        res = CFormula(self.soul_formula, self.planet_radius, self.orbit_width)
        res._x0 = self._x0
        res._y0 = self._y0
        res._compression_ratio_x, res._compression_ratio_y = self._compression_ratio_x, self._compression_ratio_y

        res._center_coordinates = self._center_coordinates.copy()
        res._centers = self._centers.copy()
        res._center_radius = self._center_radius

        res._planet_in_formula = self._planet_in_formula.copy()
        res._planet_to_angle = self._planet_to_angle.copy()
        res._orbit_label_angles = self._orbit_label_angles.copy()
        return res

    def set_center_circle_radius(self, r: float) -> None:
        self._center_radius = r

    def get_orbit_radius(self, orbit_num: int) -> float:
        return self._center_radius + orbit_num * self.orbit_width

    def get_orbit_coordinates(self, orbit_num: int) -> CircleCoordinates:
        r = self.get_orbit_radius(orbit_num)
        xk, yk = self._compression_ratio_x, self._compression_ratio_y
        return CircleCoordinates(self._x0 * xk, self._y0 * yk, r)

    def get_center_coordinates(self, i: int) -> CircleCoordinates:
        xk, yk = self._compression_ratio_x, self._compression_ratio_y
        cc = self._center_coordinates[i]
        return CircleCoordinates(cc.x * xk, cc.y * yk, cc.r)

    def set_center_coordinates(self, center_num: int, coordinates: CircleCoordinates) -> None:
        self._center_coordinates[center_num] = coordinates

    def move_centers_coordinates(self, dx: float, dy: float) -> None:
        for coordinates in self._center_coordinates:
            coordinates.x += dx
            coordinates.y += dy

    def move_coordinates(self, dx: float, dy: float, scale: float = 1.0):
        for coordinates in self._center_coordinates:
            coordinates.x = (coordinates.x + dx) * scale
            coordinates.y = (coordinates.y + dy) * scale
            coordinates.r *= scale
        self._x0 = (self._x0 + dx) * scale
        self._y0 = (self._y0 + dy) * scale

        self._center_radius *= scale
        self.orbit_width *= scale
        self.planet_radius *= scale

    def get_planet_coordinates(self, planet: str) -> CircleCoordinates:
        angle = self._planet_to_angle.get(planet)
        place, num = self._planet_in_formula.get(planet)
        xk, yk = self._compression_ratio_x, self._compression_ratio_y
        if place == 'center':
            cc = self._center_coordinates[num]
            if len(self._centers[num]) == 1:
                return CircleCoordinates(cc.x * xk, cc.y * yk, self.planet_radius)
            xp, yp = cc.x * xk + cc.r - self.planet_radius * 1.1, cc.y * yk
            x, y = rotate_point(cc.x * xk, cc.y * yk, xp, yp, angle)
            return CircleCoordinates(x, y, self.planet_radius)
        elif place == 'orbit':
            orr = self.get_orbit_radius(num)
            xp, yp = self._x0 + orr, self._y0
            x, y = rotate_point(self._x0, self._y0, xp, yp, angle)
            return CircleCoordinates(x * xk, y * yk, self.planet_radius)
        raise ValueError(f'Неизвестное расположение планеты: {place} (обрабатываем только "center" и "orbit").')

    def set_coordinates(self, x: float, y: float) -> None:
        self._x0 = x
        self._y0 = y

    def get_coordinates(self) -> (float, float):
        xk, yk = self._compression_ratio_x, self._compression_ratio_y
        return self._x0 * xk, self._y0 * yk

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

    def set_orbit_label_angles(self, angles: [float]) -> None:
        self._orbit_label_angles = angles

    def get_compress_ratio(self) -> (float, float):
        return self._compression_ratio_x, self._compression_ratio_y

    def get_orbit_label_angles(self, orbit_num) -> [float]:
        r = self.get_orbit_radius(orbit_num)
        xk, yk = self._compression_ratio_x, self._compression_ratio_y
        x, y = self._x0 + r, self._y0
        res = []
        for alpha in self._orbit_label_angles:
            xo, yo = rotate_point(self._x0, self._y0, x, y, alpha)
            res.append(CircleCoordinates(xo * xk, yo * yk, self.planet_radius * self.orbit_label_ratio))
        return res

    def get_bounds(self) -> (float, float):
        width = self._center_radius + len(self.soul_formula.orbits) * self.orbit_width
        xk, yk = self._compression_ratio_x, self._compression_ratio_y
        return width * xk, width * yk

    def compress(self):
        radiuses = [self.get_center_coordinates(i).r for i in range(len(self._centers))]
        width, height = max(radiuses), sum(radiuses)
        min_ratio = self.planet_radius * 2.7 / self.orbit_width
        if len(self.soul_formula.orbits) <= 1:
            min_ratio = 0.0
        xk = max(min_ratio, 1.2 * width / height) if width < height else 1.0
        yk = max(min_ratio, 1.2 * height / width) if height < width else 1.0
        self._compression_ratio_x, self._compression_ratio_y = xk, yk


class OptimizationLogger:

    @abstractmethod
    def log_iteration(self, c_formula: CFormula, add_info: {str, str}) -> None:
        pass

    @abstractmethod
    def start_new_optimization(self, op_type: str) -> None:
        pass


class NothingOptimizationLogger(OptimizationLogger):

    def log_iteration(self, c_formula: CFormula, add_info: {str, str}) -> None:
        pass


class PDFOptimizationLogger(OptimizationLogger):

    def log_iteration(self, c_formula: CFormula, add_info: {}) -> None:
        d_formula = convert_cformula_to_dformula(c_formula)
        iter_as_str = '{:03d}'.format(self.iter_num)
        step = add_info.get("step", 0.0)
        step_in_gradus = round(step * 180 / math.pi, 1)
        fval = add_info.get("value", 0.0)
        fval_as_str = str(round(fval, 4)) if fval < 1000 else 'inf'
        out_file = f'{self.dir_path}/iter_{add_info.get("success")}_{iter_as_str}_{self.sub_iter_num}_v{fval_as_str}_s{step_in_gradus}_{self.op_type}.pdf'
        save_formula_to_pdf(out_file, 1000, 1000, d_formula, self.drawer)

        surface_pdf = cairo.PDFSurface(out_file, 1000, 1000)
        surface_pdf.set_fallback_resolution(500, 500)
        cr = cairo.Context(surface_pdf)

        cr.scale(1000, 1000)
        drawer = SimpleFormulaDrawer()
        drawer.draw_formula(convert_cformula_to_dformula(c_formula), cr)

        if not add_info.get("success"):
            cr.set_source_rgb(1, 0, 0)

        x = 0.01
        y = 0.6
        cr.move_to(x, y)
        cr.show_text(f'Итерация {iter_as_str} / {self.sub_iter_num}, шаг={step_in_gradus}, '
                     f'успех={add_info.get("success")}: ')
        cr.stroke()
        y += 0.04
        gradient_details = add_info.get('gradient-details')
        if gradient_details:
            cr.move_to(x, y)
            cr.show_text(f'Значения градиента')
            cr.stroke()
            y += 0.02
            success_planets = add_info.get('by-planets')
            for planet, (target_angle, val1, val2, val3, res, res_final) in gradient_details.items():
                ta = target_angle * 180 / math.pi
                s = res_final * step * 180 / math.pi
                cur_angle = c_formula.get_planet_angle(planet) * 180 / math.pi
                marker = '' if planet not in success_planets else '*'
                cr.move_to(x, y)
                cr.show_text(f'{planet}{marker} : углы={round(val1, 1)}, след. орбита={round(val3, 3)}, '
                             f'расстояния={round(val2, 3)}, градиент={round(res, 1)}, '
                             f'норм. градиент={round(res_final, 1)}'
                             f', реальный шаг={round(-s, 1)}, угол={round(cur_angle, 1)}, целевой угол={round(ta, 1)}')
                cr.stroke()
                y += 0.02

        y += 0.02
        details = add_info.get('details')
        cr.move_to(x, y)
        cr.show_text(f'Значения функции = {round(fval, 6)}')
        cr.stroke()
        y += 0.02
        for planet, (val1, val2) in details.items():
            cr.move_to(x, y)
            cr.show_text(f'{planet} : углы={round(val1, 3)}, расстояния={round(val2, 3)}')
            cr.stroke()
            y += 0.02

        surface_pdf.finish()

        if add_info.get("success"):
            self.iter_num += 1
            self.sub_iter_num = 0
        else:
            self.sub_iter_num += 1

    def start_new_optimization(self, op_type: str) -> None:
        self.op_type = op_type

    def __init__(self, dir_path: str) -> None:
        dir_path = Path(dir_path)
        shutil.rmtree(dir_path, ignore_errors=True)
        dir_path.mkdir(exist_ok=True)
        self.iter_num = 0
        self.sub_iter_num = 0
        self.dir_path = dir_path
        self.drawer = SimpleFormulaDrawer()
        self.op_type = 'unknown'


class CutPolicy:

    @abstractmethod
    def cut_formula(self, c_formula: CFormula) -> CFormula:
        pass


class NothingCutPolicy(CutPolicy):

    def cut_formula(self, c_formula: CFormula) -> CFormula:
        return c_formula


class RectangleCutPolicy(CutPolicy):

    def __init__(self, width: int, height: int) -> None:
        self.height = height
        self.width = width

    def cut_formula(self, c_formula: CFormula) -> CFormula:
        min_x, min_y, max_x, max_y = \
            self._get_bounds(c_formula, length_ratio=self.width / self.height)
        scale_w, scale_h = self.width / (max_x - min_x), self.height / (max_y - min_y)
        scale = min(scale_w, scale_h)
        xk, yk = c_formula.get_compress_ratio()
        c_formula.move_coordinates(-min_x / xk, -min_y / yk, scale)

        return c_formula

    @staticmethod
    def _get_bounds(c_formula: CFormula, length_ratio=1.0, space_ratio=0.05):
        width, height = c_formula.get_bounds()
        min_x, min_y = width, height
        max_x, max_y = 0, 0
        circles: [CirclePosition] = []
        for i in range(len(c_formula.get_centers())):
            circles.append(c_formula.get_center_coordinates(i))
        for _, planets in c_formula.soul_formula.orbits.items():
            for planet in planets:
                circles.append(c_formula.get_planet_coordinates(planet))

        for cc in circles:
            min_x = min(min_x, cc.x - cc.r)
            min_y = min(min_y, cc.y - cc.r)
            max_x = max(max_x, cc.x + cc.r)
            max_y = max(max_y, cc.y + cc.r)
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


class CircleCutPolicy(CutPolicy):

    def __init__(self, radius: float, padding: float = 0.15) -> None:
        self.padding = padding
        self.radius = radius

    def cut_formula(self, c_formula: CFormula) -> CFormula:
        x, y, r = self._get_min_circle(c_formula)
        r = r * (1 + self.padding)
        min_x, min_y = x - r, y - r
        scale = self.radius / r
        xk, yk = c_formula.get_compress_ratio()
        c_formula.move_coordinates(-min_x / xk, -min_y / yk, scale)
        return c_formula

    @staticmethod
    def _get_min_circle(c_formula: CFormula) -> (float, float, float):
        circles: [CirclePosition] = []
        centers = c_formula.get_centers()
        for i in range(len(centers)):
            # circles.append(c_formula.get_center_coordinates(i))
            for planet in centers[i]:
                circles.append(c_formula.get_planet_coordinates(planet))
        for _, planets in c_formula.soul_formula.orbits.items():
            for planet in planets:
                circles.append(c_formula.get_planet_coordinates(planet))

        avg_x, avg_y = 0, 0
        for cc in circles:
            avg_x += cc.x
            avg_y += cc.y
        avg_x, avg_y = avg_x / len(circles), avg_y / len(circles)
        avg_r = 0
        for cc in circles:
            d = cc.r + math.sqrt((avg_x - cc.x) ** 2 + (avg_y - cc.y) ** 2)
            avg_r = max(avg_r, d)

        return avg_x, avg_y, avg_r


class AnglesLayoutMaker(LayoutMaker):
    planet_radius = 15
    center_padding = 5
    orbit_width = 50
    center_single_radius = 25

    def __init__(self, logger: OptimizationLogger = NothingOptimizationLogger()) -> None:
        self.logger = logger

    def make_layout(self, soul_formula: SoulFormula, width: int, height: int,
                    cut_policy: CutPolicy = NothingCutPolicy()) -> DFormula:

        best_formula = None
        for formula in self._generate_all_formulas(soul_formula):
            c_formula = self.make_start_layout(formula)

            self.logger.start_new_optimization('zero_a')
            c_formula = self._optimize_to_zero_angles(c_formula, self._get_alpha0_composite)

            c_formula = self._place_orbit_labels(c_formula)

            c_formula.compress()
            c_formula = cut_policy.cut_formula(c_formula)

            if not best_formula or c_formula.planet_radius > best_formula.planet_radius:
                best_formula = c_formula

        return convert_cformula_to_dformula(best_formula)

    @staticmethod
    def _generate_all_formulas(formula: SoulFormula) -> [SoulFormula]:
        centers = sorted(formula.center, key=lambda a: len(a))
        formula.center = centers
        center_sizes = [[i for i in range(0, len(a))] for a in formula.center]
        res = []
        for idx in itertools.product(*center_sizes):
            new_centers = []
            for i in range(len(centers)):
                cur_center = centers[i]
                start_index = idx[i]
                new_cur_center = cur_center[start_index:] + cur_center[:start_index]
                new_centers.append(new_cur_center)
            new_formula = formula.copy()
            new_formula.center = new_centers
            res.append(new_formula)
        return res

    def _place_orbit_labels(self, c_formula: CFormula) -> CFormula:
        if len(c_formula.soul_formula.orbits) == 0:
            return c_formula

        k = math.pi * 2 / 3
        angles = [
            self._get_nearest_angle(c_formula, 0),
            self._get_nearest_angle(c_formula, k),
            self._get_nearest_angle(c_formula, k * 2)
        ]
        angles = [a for a in angles if a >= 0]
        c_formula.set_orbit_label_angles(angles)

        return c_formula

    def _get_nearest_angle(self, c_formula: CFormula, angle: float) -> float:
        res = angle
        while res < math.pi * 2:
            success = True
            for orbit_num, planets in c_formula.soul_formula.orbits.items():
                min_alpha = self._get_orbit_min_angle(c_formula, orbit_num) * c_formula.orbit_label_ratio
                for planet in planets:
                    alpha = c_formula.get_planet_angle(planet)
                    if alpha - min_alpha < res < alpha + min_alpha:
                        success = False
                        break
                if not success:
                    break
            if success:
                return res
            res += 1 * math.pi / 180

        return -1

    def _optimize_to_zero_angles(self, c_formula: CFormula, target_angle_function) -> CFormula:
        # исходный шаг 30 градусов, минимальный — 1 градус
        step_min = 0.5 * math.pi / 180
        step_max = 30.0 * math.pi / 180
        step = step_max

        cur_formula = c_formula
        prev_formula = cur_formula.copy()

        prev_value, _ = self._zero_angles_function(prev_formula, target_angle_function)
        cur_value, cur_details = self._zero_angles_function(cur_formula, target_angle_function)

        is_success = self._is_success_step(cur_value, prev_value)
        self.logger.log_iteration(cur_formula,
                                  {'value': cur_value, 'success': True, 'step': step, 'details': cur_details})

        i = 100
        while (step > step_min or is_success) and i > 0:
            i -= 1

            old_prev_formula = prev_formula
            prev_formula = cur_formula.copy()
            gradient_value, gradient_details = self._zero_angles_gradient_function(cur_formula, target_angle_function)
            cur_formula, by_planets = self._move_by_gradient(cur_formula, gradient_value, step, target_angle_function)

            old_prev_value = prev_value
            prev_value = cur_value
            cur_value, cur_details = self._zero_angles_function(cur_formula, target_angle_function)

            is_success = self._is_success_step(cur_value, prev_value)

            self.logger.log_iteration(cur_formula,
                                      {'value': cur_value, 'success': is_success, 'step': step,
                                       'details': cur_details, 'gradient-details': gradient_details,
                                       'by-planets': by_planets})

            if not is_success:
                if step > step_min:
                    step /= 2

                cur_formula = prev_formula
                prev_formula = old_prev_formula

                cur_value = prev_value
                prev_value = old_prev_value

        return cur_formula

    @staticmethod
    def _is_success_step(cur_value: float, prev_value: float):
        return cur_value < prev_value and abs(cur_value - prev_value) > 0.00001

    @staticmethod
    def _get_orbit_min_angle(c_formula: CFormula, orbit_num: int) -> float:
        orbit_radius = c_formula.get_orbit_radius(orbit_num)
        alpha_min = math.asin(c_formula.planet_radius * 1.1 / 2 / orbit_radius) * 4
        return alpha_min

    @staticmethod
    def _get_alpha0_by_zero_angles(c_formula: CFormula, to_planet: str, orbit_num: int) -> float:
        x0, y0 = c_formula.get_coordinates()
        to_cc = c_formula.get_planet_coordinates(to_planet)
        orbit_radius = c_formula.get_orbit_radius(orbit_num)
        alpha0 = math.asin(abs(to_cc.y - y0) / orbit_radius)
        if to_cc.y <= y0 and to_cc.x >= x0:
            alpha0 = -alpha0
        elif to_cc.y >= y0 and to_cc.x < x0:
            alpha0 = math.pi - alpha0
        elif to_cc.y <= y0 and to_cc.x < x0:
            alpha0 = math.pi + alpha0
        return alpha0

    def _get_alpha0_by_distance(self, c_formula: CFormula, to_planet: str, orbit_num: int) -> float:
        x0, y0 = c_formula.get_coordinates()
        to_cc = c_formula.get_planet_coordinates(to_planet)
        if to_cc.x == x0:
            return self._get_alpha0_by_zero_angles(c_formula, to_planet, orbit_num)

        alpha0 = math.atan(abs(to_cc.y - y0) / abs(to_cc.x - x0))
        if to_cc.y <= y0 and to_cc.x >= x0:
            alpha0 = -alpha0
        elif to_cc.y >= y0 and to_cc.x < x0:
            alpha0 = math.pi - alpha0
        elif to_cc.y <= y0 and to_cc.x < x0:
            alpha0 = math.pi + alpha0
        return alpha0

    def _get_alpha0_composite(self, c_formula: CFormula, to_planet: str, orbit_num: int):
        if orbit_num == 1:
            return self._get_alpha0_by_zero_angles(c_formula, to_planet, orbit_num)
        return self._get_alpha0_by_distance(c_formula, to_planet, orbit_num)

    def _zero_angles_function(self, c_formula: CFormula, target_angle_function) -> (float, {str, (float, float)}):
        planet_to_value = {}
        res = 0
        for orbit_num, planets in c_formula.soul_formula.orbits.items():
            alpha_min = self._get_orbit_min_angle(c_formula, orbit_num)
            for planet in planets:
                to_planet = c_formula.soul_formula.links[planet]

                alpha0 = target_angle_function(c_formula, to_planet, orbit_num)

                cur_alpha = c_formula.get_planet_angle(planet)
                val1 = math.sin(cur_alpha - alpha0) ** 2
                res += val1
                val2 = 0
                for other_planet in planets:
                    if planet == other_planet:
                        continue
                    other_planet_alpha = c_formula.get_planet_angle(other_planet)
                    val2 += math.exp(-1000 * ((cur_alpha - other_planet_alpha) ** 2 - alpha_min ** 2))
                planet_to_value[planet] = (val1, val2)
                res += val2
        return res, planet_to_value

    def _zero_angles_gradient_function(self, c_formula: CFormula, target_angle_function) -> (
    [(str, float)], {str, (float, float, float, float, float, float)}):
        planet_to_gradient_value = {}
        target_angles = {}

        planets_order = []
        gradient_values = []

        x0, y0 = c_formula.get_coordinates()

        for orbit_num, planets in c_formula.soul_formula.orbits.items():
            alpha_min = self._get_orbit_min_angle(c_formula, orbit_num)

            cur_orbit_radius = c_formula.get_orbit_radius(orbit_num)
            next_orbit_radius = c_formula.get_orbit_radius(orbit_num + 1)

            for planet in planets:
                res = 0
                to_planet = c_formula.soul_formula.links[planet]

                alpha0 = target_angle_function(c_formula, to_planet, orbit_num)
                target_angles[planet] = alpha0

                cur_alpha = c_formula.get_planet_angle(planet)
                cur_cc = c_formula.get_planet_coordinates(planet)
                # val1 = 2 * math.sin(cur_alpha - alpha0) * math.cos(cur_alpha - alpha0)
                val1 = 2 * (cur_alpha - alpha0)
                res += val1

                val3 = 0

                for next_planet in c_formula.soul_formula.reverse_links.get(planet, []):
                    alpha_next = c_formula.get_planet_angle(next_planet)
                    alpha_next0 = target_angle_function(c_formula, planet, orbit_num + 1)
                    dd = (cur_orbit_radius / next_orbit_radius) * math.cos(cur_alpha) / math.sqrt(
                        1 - (math.sin(cur_alpha) ** 2) * (cur_orbit_radius / next_orbit_radius) ** 2)
                    if cur_cc.y > y0 and cur_cc.x >= x0:
                        dd = -dd
                    elif cur_cc.y >= y0 and cur_cc.x < x0:
                        dd = -dd
                    val3 += 2 * math.sin(alpha_next - alpha_next0) * math.cos(alpha_next - alpha_next0) * dd

                res += val3

                res1 = 0
                for other_planet in planets:
                    if planet == other_planet:
                        continue
                    other_planet_alpha = c_formula.get_planet_angle(other_planet)
                    res1 += math.exp(-1000 * ((cur_alpha - other_planet_alpha) ** 2 - alpha_min ** 2)) \
                            * (cur_alpha - other_planet_alpha)
                val2 = res1 * (-1000) * 2
                res += val2

                planet_to_gradient_value[planet] = (val1, val2, val3, res)

                planets_order.append(planet)
                gradient_values.append(res)

        gradient_len = math.sqrt(sum([a ** 2 for a in gradient_values]))
        if gradient_len != 0:
            gradient_values = [a / gradient_len for a in gradient_values]

        zipped_result = []
        for i in range(len(planets_order)):
            zipped_result.append((planets_order[i], gradient_values[i]))
        for planet, gradient_value in zipped_result:
            val1, val2, val3, res = planet_to_gradient_value[planet]
            target_angle = target_angles[planet]
            planet_to_gradient_value[planet] = (target_angle, val1, val2, val3, res, gradient_value)

        return zipped_result, planet_to_gradient_value

    def _move_by_gradient(self, c_formula: CFormula, gradient_value: [(str, float)], step: float,
                          target_angle_function) -> (CFormula, [str]):
        start_formula = c_formula.copy()
        start_value, _ = self._zero_angles_function(start_formula, target_angle_function)
        for planet, gradient_val in gradient_value:
            alpha = c_formula.get_planet_angle(planet)
            alpha += step * -gradient_val
            c_formula.set_planet_angle(planet, alpha)

        cur_value, _ = self._zero_angles_function(c_formula, target_angle_function)
        if self._is_success_step(cur_value, start_value):
            return c_formula, []

        if step > 10 * math.pi / 180:
            return c_formula, []

        success_planets = []
        for planet, gradient_val in gradient_value:
            source_alpha = start_formula.get_planet_angle(planet)
            alpha = source_alpha + step * -gradient_val
            start_formula.set_planet_angle(planet, alpha)

            cur_value, _ = self._zero_angles_function(start_formula, target_angle_function)
            if not self._is_success_step(cur_value, start_value):
                start_formula.set_planet_angle(planet, source_alpha)
            else:
                success_planets.append(planet)
        if len(success_planets) > 0:
            return start_formula, success_planets
        return c_formula, []

    def make_start_layout(self, formula: SoulFormula) -> CFormula:
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

        return c_formula

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

    @staticmethod
    def _set_centers(c: CFormula) -> (int, int):
        centers = c.soul_formula.center
        sorted_centers = sorted(centers,
                                key=lambda cc: AnglesLayoutMaker._center_power(c.soul_formula, cc), reverse=True)
        sorted_centers = [a[::-1] for a in sorted_centers]
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
                if math.pi / 2 < to_planet_alpha < math.pi * 3 / 2:
                    da = (math.pi / 2 - alpha) * 2
                c_formula.set_planet_angle(planet, alpha + da)
                alpha += alpha_step


def convert_cformula_to_dformula(c_formula: CFormula) -> DFormula:
    d_formula = DFormula(c_formula.soul_formula)
    centers = c_formula.get_centers()
    xk, yk = c_formula.get_compress_ratio()
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
        d_formula.set_orbit_position(orbit_num, OrbitPosition(oc.x, oc.y, oc.r * xk, 0, oc.r * yk, 0))

        for lc in c_formula.get_orbit_label_angles(orbit_num):
            d_formula.add_orbit_label(orbit_num, CirclePosition(lc.x, lc.y, lc.r, 0))
    return d_formula


if __name__ == '__main__':
    w, h = 1000, 1000
    dir = '/Users/mosigo/Yandex.Disk.localized/Documents/PycharmProjects/Astrogor/pic'

    builder = FlatlibBuilder()
    drawer = SimpleFormulaDrawer()

    for formula_date in ['2019-03-15 17:00 +03:00']:
    # for formula_date in ['1753-04-18 12:02 +03:00', '1986-07-14 12:02 +03:00', '2016-12-30 12:02 +03:00',
    #                      '1901-06-07 12:02 +03:00', '1939-01-28 12:02 +03:00', '1821-08-13 12:02 +03:00',
    #                      '1956-05-20 12:02 +03:00', '1987-12-04 12:02 +03:00', '1987-12-24 12:02 +03:00',
    #                      '1987-01-10 12:02 +05:00', '1992-03-19 12:02 +03:00', '1990-12-13 12:02 +03:00',
    #                      '1993-12-29 12:02 +03:00', '1996-12-17 12:02 +03:00', '1993-09-08 12:02 +03:00',
    #                      '1940-09-23 07:45 +03:00', '1991-08-20 16:51 +03:00']:
        formula = builder.build_formula(datetime.strptime(formula_date, '%Y-%m-%d %H:%M %z'))
        print(formula)

        layout_maker = AnglesLayoutMaker(PDFOptimizationLogger(f'/tmp/{formula_date[:10]}_opt'))
        # cut_policy = RectangleCutPolicy(w, h)
        cut_policy = CircleCutPolicy(500)
        # cut_policy = NothingCutPolicy()
        d_formula = layout_maker.make_layout(formula, w, h, cut_policy=cut_policy)
        print(d_formula.planet_to_position)
        print(d_formula.center_to_position)
        print(d_formula.orbit_to_position)
        print()

        save_formula_to_pdf(f"{dir}/{formula_date[:10]}_new2.pdf", w, h, d_formula, drawer)
