import math
from abc import abstractmethod
from datetime import datetime
from random import random
from typing import Callable

import cairo
from flatlib import const
from flatlib.const import ARIES, TAURUS, GEMINI, CANCER, LEO, VIRGO, LIBRA, SCORPIO, SAGITTARIUS, CAPRICORN, AQUARIUS, \
    PISCES

from model.sf import Cosmogram, SIGN_TO_HOUSE, SIGN_TO_SECOND_HOUSE, CosmogramPlanet
from model.sf_flatlib import FlatlibBuilder
from view.aspect_label import AspectLabelDrawer
from view.planet_label import PlanetLabelDrawer
from view.sf_cairo import DefaultPlanetDrawer, DrawProfile
from view.sf_geometry import rotate_point
from view.sign_label import SignLabelDrawer


class CosmogramDrawer:
    @abstractmethod
    def draw_cosmogram(self, cosmogram: Cosmogram, cr: cairo.Context):
        pass

    @abstractmethod
    def draw_aspect(self, cosmogram: Cosmogram, cr: cairo.Context, aspect: int):
        pass


class CosmogramOptimizer:
    @abstractmethod
    def make_layout(self, planet_infos: [CosmogramPlanet]) -> {str: float}:
        pass


class OptimizerLogger:
    @abstractmethod
    def log_iteration(self, i: int, status: str, prev_values: {str: float}, cur_values: {str: float}) -> None:
        pass


class DefaultCosmogramOptimizer(CosmogramOptimizer):

    def __init__(self, planet_r: float, planet_global_r: float) -> None:
        self.planet_r = planet_r
        self.planet_global_r = planet_global_r

        self.min_alpha = math.asin(self.planet_r / self.planet_global_r) * 2

    @staticmethod
    def __get_alpha_between_planets(result: {str: float},
                                    planet1: CosmogramPlanet, planet2: CosmogramPlanet) -> float:
        return abs(result[planet2.name] - result[planet1.name]) * math.pi / 180

    @staticmethod
    def __radians_to_degrees(alpha):
        return alpha * 180 / math.pi

    @staticmethod
    def __degrees_to_radians(alpha):
        return alpha * math.pi / 180

    def make_layout(self, planet_infos: [CosmogramPlanet]) -> {str: float}:
        result = {}
        buckets = {}
        for planet in planet_infos:
            result[planet.name] = planet.lon
            bucket_num = planet.lon // 30
            bucket = buckets.get(bucket_num, [])
            if len(bucket) == 0:
                buckets[bucket_num] = bucket
            bucket.append(planet)
        for bucket_num, planets in buckets.items():
            planets.sort(key=lambda p: p.lon)
            print([p.name for p in planets])

        iter_num = 1
        while iter_num <= 30:
            # print(f'Итерация {iter_num}')
            iter_num += 1
            has_moving_in_iteration = False
            for bucket_num, planets in buckets.items():
                for i in range(len(planets) - 1):
                    j = i + 1
                    alpha = self.__get_alpha_between_planets(result, planets[i], planets[j])
                    if alpha < self.min_alpha and self.min_alpha - alpha > 0.00001:
                        beta = self.__radians_to_degrees(self.min_alpha - alpha) / 2
                        # print(f'Пересечение {planets[i].name} ({result[planets[i].name]}) {planets[j].name} '
                        #       f'({result[planets[j].name]}), раздвигаем на {beta} градуса')
                        has_moving_in_iteration = True
                        for k in range(j + 1, len(planets)):
                            gamma = self.__get_alpha_between_planets(result, planets[k - 1], planets[k])
                            if gamma < self.min_alpha:
                                # print(f'Двигаем дополнительно вперёд {planets[k].name}')
                                result[planets[k].name] += beta
                            else:
                                break
                        k = i - 1
                        while k >= 0:
                            gamma = self.__get_alpha_between_planets(result, planets[k], planets[k + 1])
                            if gamma < self.min_alpha:
                                # print(f'Двигаем дополнительно назад {planets[k].name}')
                                result[planets[k].name] -= beta
                                k -= 1
                            else:
                                break
                        result[planets[i].name] -= beta
                        result[planets[j].name] += beta

                alpha0 = self.__degrees_to_radians(result[planets[0].name] - bucket_num * 30)
                if alpha0 < self.min_alpha / 2 and self.min_alpha / 2 - alpha0 > 0.00001:
                    # print(f'Планета слишком близко к границе 0: {planets[0].name}')
                    beta = self.__radians_to_degrees(self.min_alpha / 2 - alpha0)
                    result[planets[0].name] += beta
                    has_moving_in_iteration = True
                    for k in range(0, len(planets) - 1):
                        gamma = self.__get_alpha_between_planets(result, planets[k], planets[k + 1])
                        if gamma < self.min_alpha:
                            # print(f'0 Двигаем дополнительно вперёд {planets[k + 1].name}')
                            result[planets[k + 1].name] += beta
                        else:
                            break

                alphaN = ((bucket_num + 1) * 30 - result[planets[-1].name]) * math.pi / 180
                if alphaN < self.min_alpha / 2 and self.min_alpha / 2 - alphaN > 0.00001:
                    # print(f'Планета слишком близко к границе N: {planets[-1].name}')
                    beta = self.__radians_to_degrees(self.min_alpha / 2 - alphaN)
                    result[planets[-1].name] -= beta
                    has_moving_in_iteration = True
                    k = len(planets) - 1
                    while k > 0:
                        gamma = self.__get_alpha_between_planets(result, planets[k], planets[k - 1])
                        if gamma < self.min_alpha:
                            # print(f'Двигаем дополнительно назад {planets[k - 1].name}')
                            result[planets[k - 1].name] -= beta
                            k -= 1
                        else:
                            break
            if not has_moving_in_iteration:
                break

        return result


class DefaultCosmogramDrawer(CosmogramDrawer):

    def __init__(self, planet_ruler_place='inner',
                 life_years=84, first_life_year=0, first_life_year_lon=0, aspects=None,
                 draw_profile: DrawProfile = DrawProfile.DEFAULT) -> None:
        self.planet_label_drawer = PlanetLabelDrawer()
        self.planet_drawer = DefaultPlanetDrawer()
        self.sign_drawer = SignLabelDrawer()

        self.planet_ruler_place = planet_ruler_place

        self.draw_profile = draw_profile

        # знаки зодиака в нужном порядке от овна до рыб
        self.signs = [ARIES, TAURUS, GEMINI, CANCER, LEO, VIRGO, LIBRA,
                      SCORPIO, SAGITTARIUS, CAPRICORN, AQUARIUS, PISCES]

        self.main_radius = 0.49  # радиус самой внешней окружности
        self.sign_color_alpha = 0.3  # прозрачность цвета для стихии знака
        self.sign_area_width = 0.128  # ширина области, где обозначаются знаки зодиака
        self.sign_area_proportion = 0.35  # ширина внешней области (в каком соотношении разбиваем)
        self.life_years_width = 0.032  # ширина области, где выводятся годы жизни
        self.life_years = life_years  # сколько лет жизни будет выводиться
        self.first_life_year = first_life_year  # первый год жизни, который выводится (0 или 1)
        self.first_life_year_lon = first_life_year_lon  # градус первого года жизни
        self.aspects = aspects

        self.planet_radius = 0.020  # радиус планеты
        # коэффициент, на который будет умножен радиус в алгоритме укладки
        # (чтобы был зазор и планеты друг друга не касались)
        self.planet_radius_koef = 1.1
        self.planet_padding = 0.01  # расстояние между планетой и областью с годами жизни
        self.planet_projection_radius = 0.002  # радиус точечки, которая является проекцией планеты на год жизни

    def __rotate(self, x1, y1, alpha):
        cos_a = math.cos(alpha)
        sin_a = math.sin(alpha)

        x1_new = cos_a * x1 - sin_a * y1
        y1_new = sin_a * x1 + cos_a * y1

        return x1_new, y1_new

    def __draw_separators(self, cr: cairo.Context, alpha: float, inner_radius: float, outer_radius: float,
                          start_alpha: float = 0):
        a, b = -1, 0  # единичный вектор из центра влево, будем поворачивать на угол альфа именно его
        a, b = self.__rotate(a, b, -start_alpha)
        for i in range(math.floor(2 * math.pi / alpha)):
            # пользуемся матрицей поворота для преобразования координат
            # получившийся после поворота вектор добавляем к точке центра (0.5, 0.5)
            x1, y1 = 0.5 + a * inner_radius, 0.5 + b * inner_radius
            x2, y2 = 0.5 + a * outer_radius, 0.5 + b * outer_radius
            cr.move_to(x1, y1)
            cr.line_to(x2, y2)
            cr.stroke()
            # поворачиваем единичный вектор на угол альфа для следующей итерации
            a, b = self.__rotate(a, b, -alpha)

    def __draw_label(self, cr: cairo.Context, alpha: float, position_radius: float, label_radius: float,
                     draw_function: Callable[[int, cairo.Context], None], beta: float = 0, start_alpha: float = 0):
        a, b = -1, 0  # единичный вектор из центра влево, будем поворачивать на угол альфа именно его
        a, b = self.__rotate(a, b, -start_alpha)
        a, b = self.__rotate(a, b, (-alpha / 2) + beta)  # вращаем вектор на половину угла, чтобы лейбл был посередине
        for i in range(math.floor(2 * math.pi / alpha)):
            # пользуемся матрицей поворота для преобразования координат
            # получившийся после поворота вектор добавляем к точке центра (0.5, 0.5)
            x, y = 0.5 + a * position_radius, 0.5 + b * position_radius
            cr.save()
            cr.translate(x - label_radius, y - label_radius)
            cr.scale(2 * label_radius, 2 * label_radius)
            draw_function(i, cr)
            cr.restore()

            # поворачиваем единичный вектор на угол альфа для следующей итерации
            a, b = self.__rotate(a, b, -alpha)

    def __draw_sign_label(self, i: int, cr: cairo.Context) -> None:
        self.sign_drawer.draw_sign(self.signs[i], cr)

    def __draw_planet_house_label(self, i: int, cr: cairo.Context) -> None:
        self.planet_label_drawer.draw_planet(SIGN_TO_HOUSE[self.signs[i]], cr)

    def __draw_second_planet_house_label(self, i: int, cr: cairo.Context) -> None:
        planet = SIGN_TO_SECOND_HOUSE.get(self.signs[i])
        if planet:
            self.planet_label_drawer.draw_planet(planet, cr)

    def __draw_life_point(self, cr: cairo.Context, point_alpha: float, point_radius: float, start_alpha: float = 0):
        a, b = -1, 0  # единичный вектор из центра влево, будем поворачивать на угол альфа именно его
        a, b = self.__rotate(a, b, -start_alpha)  # учитываем, что старт может быть не в Овне
        a, b = self.__rotate(a, b, -point_alpha)  # вращаем вектор на половину угла, чтобы лейбл был посередине
        sign_radius = self.main_radius - self.sign_area_width
        x, y = 0.5 + a * sign_radius, 0.5 + b * sign_radius
        cr.arc(x, y, point_radius, 0, 2 * math.pi)
        cr.fill()

    def __draw_life_year(self, i: int, cr: cairo.Context) -> None:
        s = str(i + self.first_life_year)
        if len(s) == 1:
            cr.move_to(0.3, 0.68)
        else:
            cr.move_to(0.09, 0.68)
        cr.show_text(s)

    def draw_transit(self, cosmogram1: Cosmogram, cosmogram2: Cosmogram, cr: cairo.Context):
        self.draw_cosmogram(cosmogram1, cr)

        cr.set_source_rgb(0, 0, 0)

        sign_radius = self.main_radius - self.sign_area_width * 1.5
        # рисуем окружность, чтобы отделить зону знака зодиака
        cr.set_line_width(0.001)
        arc_r = self.main_radius - self.sign_area_width - self.sign_area_width * (1 - self.sign_area_proportion) * 1.1
        cr.arc(0.5, 0.5, arc_r, 0, 2 * math.pi)
        cr.stroke()

        # рисуем разделители для знаков зодиака
        self.__draw_separators(
            cr, alpha=2 * math.pi / 12, inner_radius=arc_r, outer_radius=self.main_radius - self.sign_area_width)

        # рисуем планеты транзита
        planet_radius = self._get_planet_radius(cosmogram2, sign_radius)
        planet_global_radius = self.planet_padding + sign_radius + planet_radius
        planet_lon_global_radius = sign_radius * 0.96
        projection_radius = self.main_radius - self.sign_area_width
        self._draw_cosmo_planets(cr, planet_radius, planet_global_radius, planet_lon_global_radius,
                                 projection_radius, cosmogram2)

        # рисуем текущую дату транзита
        cr.select_font_face(self.draw_profile.font_text, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        date_font_size = 0.06
        cr.set_font_size(date_font_size)
        self.add_text_by_center(cr, cosmogram2.dt.strftime('%d.%m.%Y %H:%M'), 0.5 + date_font_size * 0.8 / 2)

        # рисуем текущую точку жизни по дате транзита
        life_point = cosmogram2.get_life_point_lon()
        if life_point is not None:
            cr.set_source_rgb(0, 0, 1)
            self.__draw_life_point(cr, life_point * math.pi / 180, self.planet_projection_radius * 3)

        # отмечаем соединения
        lons = []
        for p, info in cosmogram1.planet_to_cosmogram_info.items():
            lons.append((1, info.lon))
        for p, info in cosmogram2.planet_to_cosmogram_info.items():
            lons.append((2, info.lon))
        lons = sorted(lons, key=lambda a: a[1])
        for i in range(len(lons) - 1):
            x1, lon1 = lons[i]
            x2, lon2 = lons[i+1]
            if x1 != x2 and abs(lon1 - lon2) < 1:
                lon = (lon1 + lon2) / 2
                beta = lon * math.pi / 180

                x = -projection_radius * math.cos(beta) + 0.5
                y = projection_radius * math.sin(beta) + 0.5
                r = self.planet_projection_radius * 2
                cr.set_source_rgba(1, 0, 0, 0.5)
                cr.set_line_width(0.01)
                cr.arc(x, y, r, 0, 2 * math.pi)
                cr.stroke()


    def _get_planet_radius(self, cosmogram: Cosmogram, radius):
        # вычисляем радиус планеты = минимум из заданного руками, высоты области для планет
        # и (ширина знака / кол-во планет)
        max_radius = (2 * math.pi * radius / 12) / \
                     cosmogram.get_max_planets_in_sign() / 2 / self.planet_radius_koef
        planet_radius = min(
            self.planet_radius,  # задано руками (предпочитаемый радиус)
            (self.sign_area_width * (1 - self.sign_area_proportion) - 2 * self.planet_padding) / 2,
            # но не больше, чем может поместиться по высоте
            max_radius  # планеты должны поместиться по ширине в знак зодиака
        )
        return planet_radius

    def draw_cosmogram(self, cosmogram: Cosmogram, cr: cairo.Context):
        planet_radius = self._get_planet_radius(cosmogram, self.main_radius - self.sign_area_width)

        # рисуем самую большую окружность
        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(0.001)
        cr.arc(0.5, 0.5, self.main_radius, 0, 2 * math.pi)
        cr.stroke()

        # добавляем на самую большую окружность цвета стихий
        self.__add_sign_colors(cr)

        cr.set_source_rgb(0, 0, 0)

        # рисуем окружность внутри зоны знака зодиака, которая делит эту зону пополам
        cr.set_line_width(0.0005)
        cr.arc(0.5, 0.5, self.main_radius - self.sign_area_width * self.sign_area_proportion, 0, 2 * math.pi)
        cr.stroke()

        # рисуем окружность, чтобы отделить зону знака зодиака
        sign_radius = self.main_radius - self.sign_area_width
        cr.set_line_width(0.001)
        cr.arc(0.5, 0.5, sign_radius, 0, 2 * math.pi)
        cr.stroke()

        # рисуем разделители для знаков зодиака
        self.__draw_separators(
            cr, alpha=2 * math.pi / 12, inner_radius=sign_radius, outer_radius=self.main_radius)

        # радиус для лет жизни
        life_years_radius = sign_radius - self.life_years_width

        # cтартовый угол для лет жизни
        start_alpha = self.first_life_year_lon * math.pi / 180
        if self.life_years > 0:
            # рисуем разделители для номеров года жизни
            one_sector = 360.0 / self.life_years
            self.__draw_separators(
                cr, alpha=2 * math.pi * one_sector / 360, inner_radius=life_years_radius, outer_radius=sign_radius,
                start_alpha=start_alpha
            )

            # рисуем окружность, отделяющую годы жизни
            cr.arc(0.5, 0.5, life_years_radius, 0, 2 * math.pi)
            cr.stroke()

        if self.planet_ruler_place == 'inner':

            # рисуем лейблы для планет-управителей
            cr.set_line_width(0.08)
            cr.set_source_rgb(0.8, 0.8, 0.8)
            planet_label_radius = self.main_radius - self.sign_area_width - self.sign_area_width / 2 - self.life_years_width
            second_planet_label_radius = planet_label_radius - self.sign_area_width / 2
            self.__draw_label(cr, alpha=math.pi / 6, position_radius=planet_label_radius,
                              label_radius=self.sign_area_width / 4,
                              draw_function=self.__draw_planet_house_label)
            # рисуем лейблы для вторых планет-управителей
            self.__draw_label(cr, alpha=math.pi / 6, position_radius=second_planet_label_radius,
                              label_radius=self.sign_area_width / 9,
                              draw_function=self.__draw_second_planet_house_label)

        # рисуем лейблы для знаков зодиака
        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(0.06)
        self.__draw_label(cr, alpha=math.pi / 6,
                          position_radius=self.main_radius - self.sign_area_width * self.sign_area_proportion / 2,
                          label_radius=0.015, draw_function=self.__draw_sign_label)

        if self.planet_ruler_place == 'in_sign':

            # рисуем лейблы для планет-управителей (2)
            cr.set_line_width(0.05)
            # cr.set_source_rgb(0.5, 0.5, 0.5)
            cr.set_source_rgb(0, 0, 0.8)
            self.__draw_label(cr, alpha=math.pi / 6,
                              position_radius=self.main_radius - self.sign_area_width * self.sign_area_proportion / 2,
                              label_radius=0.015,
                              draw_function=self.__draw_planet_house_label, beta=math.pi / 16)
            # рисуем лейблы для вторых планет-управителей (2)
            self.__draw_label(cr, alpha=math.pi / 6,
                              position_radius=self.main_radius - 1.2 * self.sign_area_width * self.sign_area_proportion / 2,
                              label_radius=0.008,
                              draw_function=self.__draw_second_planet_house_label, beta=math.pi / 25)

        planet_global_radius = self.planet_padding + sign_radius + planet_radius
        planet_lon_global_radius = (self.main_radius - self.sign_area_width * self.sign_area_proportion) * 0.96
        self._draw_cosmo_planets(cr, planet_radius,
                                 planet_global_radius, planet_lon_global_radius, sign_radius, cosmogram)

        life_point = cosmogram.get_life_point_lon()
        death_point = cosmogram.get_death_point_lon()

        # закрашиваем годы жизни
        if (life_point or death_point) and self.life_years > 0:
            point = life_point if death_point is None else death_point
            alpha = point * math.pi / 180
            cr.set_line_width(self.life_years_width)
            lp_r = life_years_radius + 0.5 * self.life_years_width
            gray_alpha = 0.5
            while alpha > 0:
                cr.set_source_rgba(1, 1, 0, gray_alpha)
                cr.arc_negative(0.5, 0.5, lp_r, math.pi, math.pi - alpha)
                cr.stroke()
                alpha -= 2 * math.pi
                gray_alpha += 0.2

        cr.set_line_width(0.001)

        if self.life_years > 0:
            # рисуем лейблы для лет жизни
            cr.set_font_size(self.life_years_width * 23)
            cr.set_source_rgb(0, 0, 0)
            cr.select_font_face(self.draw_profile.font_text, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            self.__draw_label(cr, alpha=2 * math.pi / self.life_years,
                              position_radius=life_years_radius + self.life_years_width / 2, label_radius=0.01,
                              draw_function=self.__draw_life_year,
                              start_alpha=start_alpha)
            cr.stroke()

        # рисуем текущую точку жизни
        if life_point is not None:
            cr.set_source_rgb(0, 0, 1)
            self.__draw_life_point(cr, life_point * math.pi / 180, self.planet_projection_radius * 2,
                                   start_alpha=start_alpha)

        # рисуем точку смерти, если она есть
        if death_point is not None:
            cr.set_source_rgb(0, 0, 0)
            self.__draw_life_point(cr, death_point * math.pi / 180, self.planet_projection_radius * 3,
                                   start_alpha=start_alpha)

        # рисуем аспекты, если они заданы
        if self.aspects:
            x, y = 0.5, 0.5
            r = life_years_radius
            drawer = AspectLabelDrawer()
            cr.set_line_width(0.001)
            cr.set_line_cap(cairo.LINE_CAP_ROUND)
            for aspect in self.aspects:
                drawer.set_aspect_color(aspect, cr)
                for p1, others in self._build_planet_aspects(cosmogram, aspect).items():
                    for p2 in others:
                        pi1, pi2 = cosmogram.get_planet_info(p1), cosmogram.get_planet_info(p2)
                        x1, y1 = rotate_point(x, y, 0.5 - r, 0.5, -pi1.lon * math.pi / 180)
                        x2, y2 = rotate_point(x, y, 0.5 - r, 0.5, -pi2.lon * math.pi / 180)
                        cr.move_to(x1, y1)
                        cr.line_to(x2, y2)
                        cr.stroke()
                # рисуем лейлбл аспекта внутри круга
                # сначала белый фон
                cr.set_source_rgb(1, 1, 1)
                cr.save()
                cr.set_line_width(0.3)
                label_radius = 0.6 * 0.1
                cr.translate(0.5 - label_radius, 0.5 - label_radius)
                cr.scale(2 * label_radius, 2 * label_radius)
                drawer.draw_aspect(aspect, cr, default_color=False)
                cr.restore()

                # на белом фоне выводим иконку аспекта
                cr.save()
                cr.set_line_width(0.1)
                label_radius = 0.6 * 0.1
                cr.translate(0.5 - label_radius, 0.5 - label_radius)
                cr.scale(2 * label_radius, 2 * label_radius)
                drawer.draw_aspect(aspect, cr)
                cr.restore()

            cr.set_source_rgb(0, 0, 0)
            rp = self.planet_projection_radius
            for p in cosmogram.get_planets():
                xp, yp = rotate_point(x, y, 0.5 - r, 0.5, -p.lon * math.pi / 180)
                cr.arc(xp, yp, rp, 0, 2 * math.pi)
                cr.fill()

    def _draw_cosmo_planets(self, cr: cairo.Context, planet_radius,
                            planet_global_radius, planet_lon_global_radius, projection_radius,
                            cosmogram: Cosmogram):
        planet_optimizer = DefaultCosmogramOptimizer(planet_radius * self.planet_radius_koef, planet_global_radius)
        all_planets = cosmogram.get_planets()
        planet_to_lon = planet_optimizer.make_layout(all_planets)
        for planet, lon in planet_to_lon.items():
            beta_planet = lon * math.pi / 180
            beta_projection = cosmogram.get_planet_info(planet).lon * math.pi / 180

            # координаты самой планеты
            x = -planet_global_radius * math.cos(beta_planet) + 0.5
            y = planet_global_radius * math.sin(beta_planet) + 0.5
            r = planet_radius

            # координаты проекции
            x1 = -projection_radius * math.cos(beta_projection) + 0.5
            y1 = projection_radius * math.sin(beta_projection) + 0.5
            r1 = self.planet_projection_radius

            # координаты точки, куда будет выводится долгота планеты
            x2 = -planet_lon_global_radius * math.cos(beta_planet) + 0.5
            y2 = planet_lon_global_radius * math.sin(beta_planet) + 0.5

            # рисуем линию между планетой и её проекцией на годы жизни
            cr.set_source_rgb(0.5, 0.5, 0.5)
            cr.set_line_width(0.001)
            cr.move_to(x, y)
            cr.line_to(x1, y1)
            cr.stroke()

            # рисуем точечку-проекцию планеты на годы жизни
            cr.set_source_rgb(0, 0, 0)
            cr.set_line_width(0.001)
            cr.arc(x1, y1, r1, 0, 2 * math.pi)
            cr.fill()

            # рисуем саму планету
            planet_info = cosmogram.get_planet_info(planet)
            is_additional = planet_info in cosmogram.additional_planets
            power = planet_info.power
            if is_additional:
                power = None
                r = r * 0.9
            cr.set_line_width(0.003)
            self.planet_drawer.draw_planet(planet, cr, x, y, r,
                                           is_retro=planet_info.movement == const.RETROGRADE,
                                           power=power, is_selected=is_additional, label_line_width=0.1)

            # рисуем долготу планеты цифрами
            cr.set_source_rgb(0, 0, 0)
            cr.set_font_size(0.015)
            cr.select_font_face(self.draw_profile.font_text, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            lon_as_str = str(math.ceil(planet_info.signlon)) + '°'
            if len(lon_as_str) == 3:
                x2 -= 0.012
                y2 += 0.004
            else:
                x2 -= 0.008
                y2 += 0.004
            cr.move_to(x2, y2)
            cr.show_text(lon_as_str)
            cr.stroke()

    def __add_sign_color(self, cr: cairo.Context, start_psi: float, r, g, b):
        psi = start_psi
        for i in range(3):
            cr.set_source_rgba(r, g, b, self.sign_color_alpha)
            cr.set_line_width(self.sign_area_width * self.sign_area_proportion)
            cr.arc(0.5, 0.5, self.main_radius - self.sign_area_width * self.sign_area_proportion / 2, psi, psi + math.pi / 6)
            cr.stroke()

            cr.set_source_rgba(r, g, b, self.sign_color_alpha / 3)
            cr.set_line_width(self.sign_area_width * (1 - self.sign_area_proportion))
            cr.arc(0.5, 0.5, self.main_radius - self.sign_area_width * self.sign_area_proportion
                   - self.sign_area_width * (1 - self.sign_area_proportion) / 2, psi, psi + math.pi / 6)
            cr.stroke()
            psi += 2 * math.pi / 3

    def __add_sign_colors(self, cr: cairo.Context):
        self.__add_sign_color(cr, start_psi=0, r=0, g=1, b=0)
        self.__add_sign_color(cr, start_psi=math.pi / 6, r=1, g=0, b=0)
        self.__add_sign_color(cr, start_psi=math.pi / 3, r=0, g=0, b=1)
        self.__add_sign_color(cr, start_psi=math.pi / 2, r=1, g=1, b=0)

    @staticmethod
    def _build_planet_aspects(cosmogram: Cosmogram, aspect: int):
        res = {}
        for p1, planet_aspects in cosmogram.planet_to_aspect.items():
            for p2, p_aspect in planet_aspects:
                if p_aspect == aspect:
                    others = res.get(p1, [])
                    if len(others) == 0:
                        res[p1] = others
                    others.append(p2)
        return res

    def draw_aspect_shape(self, cosmogram: Cosmogram, cr: cairo.Context):
        x, y = 0.5, 0.5
        r = 0.45
        rp = 0.01

        # рисуем окружность, на которой будем выводить планеты в виде точек
        cr.set_line_width(0.001)
        cr.set_source_rgb(0, 0, 0)
        cr.arc(x, y, r, 0, 2 * math.pi)
        cr.stroke()

        # выводим аспекты линиями соответствующего цвета
        drawer = AspectLabelDrawer()
        cr.set_line_width(0.005)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        for p1, planet_aspects in cosmogram.planet_to_aspect.items():
            for p2, p_aspect in planet_aspects:
                drawer.set_aspect_color(p_aspect, cr)
                pi1, pi2 = cosmogram.get_planet_info(p1), cosmogram.get_planet_info(p2)
                x1, y1 = rotate_point(x, y, 0.5 - r, 0.5, -pi1.lon * math.pi / 180)
                x2, y2 = rotate_point(x, y, 0.5 - r, 0.5, -pi2.lon * math.pi / 180)
                cr.move_to(x1, y1)
                cr.line_to(x2, y2)
                cr.stroke()

        # выводим планеты в виде мелких точек
        cr.set_source_rgb(0, 0, 0)
        for p in cosmogram.get_planets():
            xp, yp = rotate_point(x, y, 0.5 - r, 0.5, -p.lon * math.pi / 180)
            cr.arc(xp, yp, rp, 0, 2 * math.pi)
            cr.fill()

    @staticmethod
    def _year_name(x, labels):
        y1 = x % 100
        if 11 <= y1 <= 19:
            return labels[0]  # 'лет', 'дней'
        y = x % 10
        if y == 1:
            return labels[1]  # 'год', 'день'
        if 2 <= y <= 4:
            return labels[2]  # 'года', 'дня'
        return labels[0]  # 'лет', 'дней'

    @staticmethod
    def _format_int(x):
        s1 = str(x)[::-1]
        s2 = s1[:3]
        s1 = s1[3:]
        while len(s1) > 0:
            s2 += ' '
            s2 += s1[:3]
            s1 = s1[3:]
        return s2[::-1]

    def add_text_by_center(self, cr: cairo.Context, text, y):
        te = cr.text_extents(text)
        x = (1 - te.width) / 2
        cr.move_to(x, y)
        cr.show_text(text)
        cr.stroke()

    def draw_current_day(self, today: datetime, cosmogram: Cosmogram, cr: cairo.Context, age_units='days'):
        cr.set_line_width(0.002)

        cr.select_font_face(self.draw_profile.font_text, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        font_size = 0.10
        cr.set_font_size(font_size)
        today_str = today.strftime("%d.%m.%Y в %H:%M мск")
        te = cr.text_extents(today_str)
        while te.width > 0.9:
            font_size *= 0.99
            cr.set_font_size(font_size)
            te = cr.text_extents(today_str)
        self.add_text_by_center(cr, today_str, 0.36)
        n = cosmogram.get_life_years()
        m = cosmogram.get_life_days()
        y = self._year_name(n, ['лет', 'год', 'года'])
        d = self._year_name(m, ['дней', 'день', 'дня'])

        cr.select_font_face(self.draw_profile.font_text, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        self.add_text_by_center(cr, 'от рождения прошло', 0.55)
        if cosmogram.death_dt:
            self.add_text_by_center(cr, f"{n} {y}", 0.67)
            self.add_text_by_center(cr, f"{self._format_int(m)} {d}", 0.79)
            cr.stroke()
        else:
            if age_units == 'days':
                self.add_text_by_center(cr, f'{d}', 0.85)
                cr.set_font_size(0.12)
                self.add_text_by_center(cr, f"{self._format_int(m)}", 0.72)
            elif age_units == 'years':
                self.add_text_by_center(cr, f'{y}', 0.85)
                cr.set_font_size(0.12)
                self.add_text_by_center(cr, f"{self._format_int(n)}", 0.72)

        cr.set_line_width(0.002)
        cr.move_to(0.1, 0.43)
        cr.line_to(0.9, 0.43)
        cr.stroke()

        cr.select_font_face(self.draw_profile.font_header, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.move_to(0.23, 0.22)
        cr.set_font_size(0.085)
        self.add_text_by_center(cr, 'Построено', 0.22)
        cr.stroke()

    def draw_aspect(self, cosmogram: Cosmogram, cr: cairo.Context, aspect: int, highlight=False):
        # достаём данные только по заданному аспекту
        planet_to_other = self._build_planet_aspects(cosmogram, aspect)

        # считаем угол, под которым будут расположены две планеты друг к другу
        alpha = 2 * math.pi / len(planet_to_other.keys()) if planet_to_other else 0
        r = math.pi * 0.45 / len(planet_to_other) / 1.2 if planet_to_other else 0.1
        r = min(0.1, r)
        x, y = r + 0.05, 0.5
        r1 = 0.5 - 0.05 - 2 * r
        x1, y1 = (0.5 - r1), 0.5
        planet_links = sorted(list(planet_to_other.items()), key=lambda p: cosmogram.get_planet_info(p[0]).lon)
        # вычисляем точку для каждой планеты, по которой будет соединение (в неё будет вести линия)
        planet_to_connection_point = {}
        for p1, planets in planet_links:
            x1, y1 = rotate_point(0.5, 0.5, x1, y1, -alpha)
            planet_to_connection_point[p1] = x1, y1

        # рисуем серый толстый кружочек
        cr.stroke()
        cr.set_source_rgb(0.9, 0.9, 0.9)
        cr.set_line_width(0.05)
        cr.arc(0.5, 0.5, r1 - 0.025, 0, 2 * math.pi)
        cr.stroke()

        drawer = AspectLabelDrawer()

        # выставляем цвет аспекта и настройки толщины линии
        drawer.set_aspect_color(aspect, cr)
        cr.set_line_width(0.005)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)

        # рисуем соединения между планетами
        for p1, planets in planet_links:
            x0, y0 = planet_to_connection_point[p1]
            for p2 in planets:
                x2, y2 = planet_to_connection_point[p2]
                info1 = cosmogram.get_planet_info(p1)
                info2 = cosmogram.get_planet_info(p2)
                lon1, lon2 = info1.lon, info2.lon
                if lon1 - lon2 > 180:
                    lon2 += 360
                elif lon2 - lon1 > 180:
                    lon1 += 360
                if highlight:
                    if abs(info1.signlon - info2.signlon) < 1:
                        cr.set_line_width(0.04)
                    elif lon1 > lon2 and info1.signlon < info2.signlon:
                        cr.set_line_width(0.015)
                    else:
                        cr.set_line_width(0.002)
                cr.move_to(x0, y0)
                cr.line_to(x2, y2)
                cr.stroke()

        # рисуем лейлбл аспекта внутри круга
        # сначала белый фон
        cr.set_source_rgb(1, 1, 1)
        cr.save()
        cr.set_line_width(0.3)
        label_radius = 0.6 * 0.1
        cr.translate(0.5 - label_radius, 0.5 - label_radius)
        cr.scale(2 * label_radius, 2 * label_radius)
        drawer.draw_aspect(aspect, cr, default_color=False)
        cr.restore()

        # на белом фоне выводим иконку аспекта
        cr.save()
        cr.set_line_width(0.1)
        label_radius = 0.6 * 0.1
        cr.translate(0.5 - label_radius, 0.5 - label_radius)
        cr.scale(2 * label_radius, 2 * label_radius)
        drawer.draw_aspect(aspect, cr)
        cr.restore()

        # рисуем сами планеты
        for p1, planets in planet_links:
            x, y = rotate_point(0.5, 0.5, x, y, -alpha)
            planet_info = cosmogram.get_planet_info(p1)
            is_additional = planet_info in cosmogram.additional_planets
            power = planet_info.power

            if is_additional:
                power = None
            self.planet_drawer.draw_planet(p1, cr, x, y, r,
                                           is_retro=planet_info.movement == const.RETROGRADE,
                                           power=power, is_selected=is_additional)

    def draw_aspect1(self, cosmogram: Cosmogram, cr: cairo.Context, aspect: int):
        planet_to_other = {}
        for p1, planet_aspects in cosmogram.planet_to_aspect.items():
            for p2, p_aspect in planet_aspects:
                if p_aspect == aspect:
                    others = planet_to_other.get(p1, [])
                    if len(others) == 0:
                        planet_to_other[p1] = others
                    others.append(p2)
        res = sorted([a for a in planet_to_other.items()], key=lambda a: len(a[1]), reverse=True)
        rows = len(res)
        cols = max([len(a[1]) for a in res]) + 1

        # рисуем линию, отделяющую планету от тех, с кем у неё аспект
        cr.move_to(1 / cols, 0)
        cr.line_to(1 / cols, 1)
        cr.stroke()

        # рисуем сами планеты
        x, y = 0.5 / cols, 0.5 / rows
        r = (0.5 / max(cols, rows)) * 0.9
        for p1, planets in res:
            planet_info = cosmogram.get_planet_info(p1)
            is_additional = planet_info in cosmogram.additional_planets
            power = planet_info.power

            if is_additional:
                power = None
            self.planet_drawer.draw_planet(p1, cr, x, y, r,
                                           is_retro=planet_info.movement == const.RETROGRADE,
                                           power=power, is_selected=is_additional)
            for p2 in planets:
                x += 1 / cols

                planet_info2 = cosmogram.get_planet_info(p2)
                is_additional = planet_info2 in cosmogram.additional_planets
                power = planet_info2.power

                if is_additional:
                    power = None
                self.planet_drawer.draw_planet(p2, cr, x, y, r,
                                               is_retro=planet_info2.movement == const.RETROGRADE,
                                               power=power, is_selected=is_additional)
            x = 0.5 / cols
            y += 1 / rows


def draw_cosmo(dt: datetime):
    dir = '/Users/mosigo/Yandex.Disk.localized/Documents/PycharmProjects/Astrogor/pic'
    surface_pdf = cairo.PDFSurface(f"{dir}/cosmo.pdf", 200, 200)
    cr = cairo.Context(surface_pdf)
    cr.scale(200, 200)

    builder = FlatlibBuilder()
    cosmo = builder.build_cosmogram(
        dt
    )

    drawer = DefaultCosmogramDrawer(planet_ruler_place='in_sign', life_years=1)
    drawer.draw_cosmogram(cosmo, cr)
    surface_pdf.finish()


def draw_transit(dt1: datetime, dt2: datetime):
    dir = '/Users/mosigo/Yandex.Disk.localized/Documents/PycharmProjects/Astrogor/pic'
    surface_pdf = cairo.PDFSurface(f"{dir}/cosmo_transit.pdf", 200, 200)
    cr = cairo.Context(surface_pdf)
    cr.scale(200, 200)

    builder = FlatlibBuilder()
    # cosmo1 = builder.build_cosmogram(dt_from, lon=68.253771, lat=58.201698)
    cosmo1 = builder.build_cosmogram(dt1, lon=73.368221, lat=54.989347)
    # cosmo1 = builder.build_cosmogram(dt_from)
    cosmo2 = builder.build_cosmogram(dt2)

    drawer = DefaultCosmogramDrawer(planet_ruler_place='in_sign', life_years=0)
    drawer.draw_transit(cosmo1, cosmo2, cr)
    surface_pdf.finish()


if __name__ == '__main__':
    # draw_cosmo(datetime.strptime('1991-08-20 16:31 +03:00', '%Y-%m-%d %H:%M %z'))
    # draw_transit(
    #     datetime.strptime('1987-01-10 12:00 +05:00', '%Y-%m-%d %H:%M %z'),
    #     datetime.strptime('2021-12-20 12:00 +03:00', '%Y-%m-%d %H:%M %z')
    # )

    draw_transit(
        datetime.strptime('1992-03-19 12:00 +06:00', '%Y-%m-%d %H:%M %z'),
        datetime.strptime('2022-02-02 12:00 +03:00', '%Y-%m-%d %H:%M %z')
    )
