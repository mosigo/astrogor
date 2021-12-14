from abc import abstractmethod
from random import random

import cairo
import math

from view.sf_cairo import DFormula, CirclePosition, OrbitPosition


class Optimization:
    @abstractmethod
    def optimize(self, d_formula: DFormula, cr: cairo.Context) -> DFormula:
        pass


class GradientOptimization(Optimization):
    def optimize_by_one(self, d_formula: DFormula, cr: cairo.Context) -> None:
        orbit_planets = []
        for orbit_num, planets in d_formula.formula.orbits.items():
            orbit_planets += planets
        if len(orbit_planets) == 0:  # если нет планет на орбитах
            return

        old_function_value = self.__optimization_function_value(d_formula)
        max_step_size = 2 * min([a.get_radius_device() for a in d_formula.planet_to_position.values()])
        step_size = max_step_size

        iteration_cnt = 0
        planet_to_optimize_idx = 0
        while True:
            iteration_cnt += 1
            # print(f'Планета, которую двигаем: {orbit_planets[planet_to_optimize_idx]}')
            df = self.__optimization_function_gradient_value(d_formula)

            planet = orbit_planets[planet_to_optimize_idx]
            orbit_pos = self.__get_orbit_pos(planet, d_formula)

            x0, y0 = orbit_pos.get_center_device()
            rw = orbit_pos.get_w_radius_device()
            rh = orbit_pos.get_h_radius_device()

            pos = d_formula.get_planet_position(planet)
            x, y = pos.get_center_device()
            prev_x = x
            r = pos.get_radius_device()
            dy = df[planet] * step_size
            y -= dy
            y = max(y0 - rh, y)
            y = min(y0 + rh, y)
            v = max(0, 1 - ((y - y0) ** 2) / (rh ** 2))
            x = rw * math.sqrt(v)
            if prev_x < x0:
                x = -x
            x += x0
            new_pos = CirclePosition(x, y, r, 0)
            d_formula.set_planet_position(planet, new_pos)
            new_function_value = self.__optimization_function_value(d_formula)

            # print(f'Новое значение функции: {new_function_value}, старое: {old_function_value}.')

            if new_function_value >= old_function_value \
                    and planet_to_optimize_idx == len(orbit_planets) - 1 and step_size < 1:
                # print(f'Оптимизация окончена.')
                d_formula.set_planet_position(planet, pos)
                return
            if new_function_value < old_function_value:
                # print('Совершили успешный шаг, сбрасываем планету для оптимизации.')
                planet_to_optimize_idx = 0
                old_function_value = new_function_value
                step_size = max_step_size
            elif step_size >= 1:
                step_size /= 2
                planet_to_optimize_idx = 0
                d_formula.set_planet_position(planet, pos)
                # print(f'Успешных шагов нет ни по одной планете, пробуем уменьшить шаг => {step_size}')
            else:
                # print('Шаг не успешен, берём следующую планету для оптимизации.')
                # print(f'\tбыло : {pos}')
                # print(f'\tстало: {new_pos}')
                d_formula.set_planet_position(planet, pos)
                planet_to_optimize_idx += 1

    @staticmethod
    def __get_orbit_pos(planet, d_formula):
        for orbit_num, orbit_pos in d_formula.orbit_to_position.items():
            planets = d_formula.formula.orbits[orbit_num]
            for p in planets:
                if p == planet:
                    return orbit_pos

    def optimize(self, d_formula: DFormula, cr: cairo.Context) -> None:
        print('оптимизация 1')
        self.optimize_all(d_formula, cr)
        print('оптимизация 2')
        self.optimize_by_one(d_formula, cr)
        print('оптимизация 3')
        self.optimize_all(d_formula, cr)

    def optimize_all(self, d_formula: DFormula, cr: cairo.Context) -> None:
        old_function_value = self.__optimization_function_value(d_formula)
        if old_function_value == 0:  # если нет планет на орбитах
            return

        max_step_size = 2 * min([a.get_radius_device() for a in d_formula.planet_to_position.values()])
        step_size = max_step_size
        iteration_cnt = 0
        while True:
            iteration_cnt += 1
            df = self.__optimization_function_gradient_value(d_formula)
            planet_to_old_pos = {}
            for orbit_num, orbit_pos in d_formula.orbit_to_position.items():
                planets = d_formula.formula.orbits[orbit_num]
                for planet in planets:
                    x0, y0 = orbit_pos.get_center_device()
                    rw = orbit_pos.get_w_radius_device()
                    rh = orbit_pos.get_h_radius_device()

                    pos = d_formula.get_planet_position(planet)
                    planet_to_old_pos[planet] = pos
                    x, y = pos.get_center_device()
                    x_prev, y_prev = x, y
                    r = pos.get_radius_device()
                    dy = df[planet] * step_size
                    if dy == 0:
                        to_planet = d_formula.formula.links[planet]
                        x_to, y_to = d_formula.get_planet_position(to_planet).get_center_device()
                        if abs(x - x0) < 0.001 and abs(x_to - x0) < 0.001:
                            if random() >= 0.5:
                                if y > y0:
                                    dy = r / 10
                                else:
                                    dy = -r / 10

                        elif abs(y - y0) < 0.001 and abs(y_to - y0) < 0.001:
                            if random() >= 0.5:
                                dy = r / 10
                                if random() >= 0.5:
                                    dy *= -1

                    y -= dy
                    y = max(y0 - rh, y)
                    y = min(y0 + rh, y)
                    v = max(0, 1 - ((y - y0) ** 2) / (rh ** 2))

                    x = rw * math.sqrt(v)
                    if x_prev < x0:
                        x = -x
                    elif x_prev == x0:
                        if random() >= 0.5:
                            x = -x
                    x += x0
                    d_formula.set_planet_position(planet, CirclePosition(x, y, r, 0))

            # print(f'Значение функции {iteration_cnt - 1} = {old_function_value}, шаг = {step_size}.')
            new_function_value = self.__optimization_function_value(d_formula)
            if new_function_value > old_function_value:
                # print(f'Новое значение функции больше старого: {new_function_value} > {old_function_value}.')
                for planet, pos in planet_to_old_pos.items():
                    # print(planet)
                    # print(f'\tбыло:  {pos}')
                    # print(f'\tстало: {d_formula.get_planet_position(planet)}')
                    d_formula.set_planet_position(planet, pos)
                if step_size <= 0.001:
                    # print('Оптимизация окончена.')
                    return
                step_size /= 2
            else:
                old_function_value = new_function_value
                if step_size < max_step_size:
                    step_size *= 2

    @staticmethod
    def __get_distance_between_planets(planet1: str, planet2: str, d_formula: DFormula, with_radius=True) -> float:
        pos1 = d_formula.get_planet_position(planet1)
        pos2 = d_formula.get_planet_position(planet2)
        x1, y1 = pos1.get_center_device()
        r1 = pos1.get_radius_device() * 1.15
        x2, y2 = pos2.get_center_device()
        r2 = pos2.get_radius_device() * 1.15
        d = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        # print('Расстояние', planet1, planet2, d - r1 - r2 if with_radius else d)
        if with_radius:
            return d - r1 - r2
        return d

    def __get_gradient_distance_between_planets(self, orbit_num: int, planet: str, planet2: str,
                                                d_formula: DFormula) -> float:
        pos1 = d_formula.get_planet_position(planet)
        pos2 = d_formula.get_planet_position(planet2)
        x1, y1 = pos1.get_center_device()
        x2, y2 = pos2.get_center_device()

        orbit_pos = d_formula.get_orbit_position(orbit_num)
        x0, y0 = orbit_pos.get_center_device()
        rw = orbit_pos.get_w_radius_device()
        rh = orbit_pos.get_h_radius_device()

        k = -1 if x1 < x0 else 1

        v = 1 - ((y1 - y0) ** 2) / (rh ** 2)

        if v > 0:
            dx1 = -rw * (y1 - y0) * k / ((rh ** 2) * math.sqrt(v))
            return - (y2 - y1 + (x2 - x1) * dx1) / self.__get_distance_between_planets(planet, planet2, d_formula,
                                                                                       with_radius=False)
        return 0

    def __optimization_function_value(self, d_formula: DFormula) -> float:
        value = 0
        z = 10
        for orbit_num, orbit_pos in d_formula.orbit_to_position.items():
            orbit_planets = d_formula.formula.orbits[orbit_num]
            orbit_planets_cnt = len(orbit_planets)
            for i in range(orbit_planets_cnt):
                cur_planet = orbit_planets[i]
                value += self.__get_distance_between_planets(cur_planet, d_formula.formula.links[cur_planet], d_formula)
                for j in range(i + 1, orbit_planets_cnt):
                    to_planet = orbit_planets[j]
                    val = math.exp(-z * self.__get_distance_between_planets(cur_planet, to_planet, d_formula))
                    # print('Вклад в расстояние', cur_planet, to_planet, val)
                    value += val
        return value

    def __optimization_function_gradient_value(self, d_formula: DFormula):
        z = 10
        planet_to_df = {}
        for orbit_num, orbit_pos in d_formula.orbit_to_position.items():
            orbit_planets = d_formula.formula.orbits[orbit_num]
            orbit_planets_cnt = len(orbit_planets)
            for i in range(orbit_planets_cnt):
                cur_planet = orbit_planets[i]
                value = self.__get_gradient_distance_between_planets(
                    orbit_num, cur_planet, d_formula.formula.links[cur_planet], d_formula)
                for j in range(i + 1, orbit_planets_cnt):
                    to_planet = orbit_planets[j]
                    value += math.exp(
                        -z * self.__get_distance_between_planets(cur_planet, to_planet, d_formula)) \
                             * (-z) * self.__get_gradient_distance_between_planets(orbit_num, cur_planet, to_planet,
                                                                                   d_formula)
                planet_to_df[cur_planet] = value
        df_len = 0
        for planet, df in planet_to_df.items():
            df_len += df ** 2
        df_len = math.sqrt(df_len)
        if df_len > 0:
            for planet, df in planet_to_df.items():
                planet_to_df[planet] = df / df_len
        return planet_to_df


class CornerOptimization(Optimization):

    def __init__(self) -> None:
        self.z = 10  # коэффециент в степени экспаненты для штрафа за пересечения

    def optimize(self, d_formula: DFormula, cr: cairo.Context) -> DFormula:
        pass

        planet_to_alpha = {}
        for orbit_num, orbit_pos in d_formula.orbit_to_position.items():
            orbit_planets = d_formula.formula.orbits[orbit_num]
            orbit_planets_cnt = len(orbit_planets)
            for i in range(orbit_planets_cnt):
                cur_planet = orbit_planets[i]

                pos = d_formula.get_planet_position(cur_planet)
                x, y = pos.get_center_device()
                r = pos.get_radius_device() * 1.15



    def _optimization_function_value(self, d_formula):
        value = 0
        for orbit_num, orbit_pos in d_formula.orbit_to_position.items():
            orbit_planets = d_formula.formula.orbits[orbit_num]
            orbit_planets_cnt = len(orbit_planets)
            for i in range(orbit_planets_cnt):
                cur_planet = orbit_planets[i]
                value += self.__get_distance_between_planets(cur_planet, d_formula.formula.links[cur_planet], d_formula)
                for j in range(i + 1, orbit_planets_cnt):
                    to_planet = orbit_planets[j]
                    val = math.exp(-self.z * self.__get_distance_between_planets(cur_planet, to_planet, d_formula))
                    value += val
        return value

    def _optimization_function_gradient_value(self, d_formula: DFormula):
        z = 10
        planet_to_df = {}
        for orbit_num, orbit_pos in d_formula.orbit_to_position.items():
            orbit_planets = d_formula.formula.orbits[orbit_num]
            orbit_planets_cnt = len(orbit_planets)
            for i in range(orbit_planets_cnt):
                cur_planet = orbit_planets[i]
                value = self.__get_gradient_distance_between_planets(
                    orbit_num, cur_planet, d_formula.formula.links[cur_planet], d_formula)
                for j in range(i + 1, orbit_planets_cnt):
                    to_planet = orbit_planets[j]
                    value += math.exp(
                        -z * self.__get_distance_between_planets(cur_planet, to_planet, d_formula)) \
                             * (-z) * self.__get_gradient_distance_between_planets(orbit_num, cur_planet, to_planet,
                                                                                   d_formula)
                planet_to_df[cur_planet] = value
        df_len = 0
        for planet, df in planet_to_df.items():
            df_len += df ** 2
        df_len = math.sqrt(df_len)
        if df_len > 0:
            for planet, df in planet_to_df.items():
                planet_to_df[planet] = df / df_len
        return planet_to_df

    def __get_gradient_distance_between_planets(self, orbit_num: int, planet1: str, planet2: str,
                                                d_formula: DFormula) -> float:
        pass