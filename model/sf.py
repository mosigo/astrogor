from abc import abstractmethod

import pytz
from flatlib import const
from datetime import datetime, timedelta

from flatlib.const import MAJOR_ASPECTS

PLANET_TO_CHAR = {
    const.SUN: '☉', const.MOON: '☽',
    const.MERCURY: '☿', const.VENUS: '♀', const.MARS: '♂', const.JUPITER: '♃', const.SATURN: '♄',
    const.URANUS: '♅', const.NEPTUNE: '♆', const.PLUTO: '⚘',
    const.CHIRON: '⥉', const.NORTH_NODE: '☊', const.PARS_FORTUNA: '⊛', 'Lilith': '●', 'Selena': '○'
}

SIGN_TO_HOUSE = {
    const.ARIES: const.MARS,
    const.TAURUS: const.VENUS,
    const.GEMINI: const.MERCURY,
    const.CANCER: const.MOON,
    const.LEO: const.SUN,
    const.VIRGO: const.MERCURY,
    const.LIBRA: const.VENUS,
    const.SCORPIO: const.PLUTO,
    const.SAGITTARIUS: const.JUPITER,
    const.CAPRICORN: const.SATURN,
    const.AQUARIUS: const.URANUS,
    const.PISCES: const.NEPTUNE
}

SIGN_TO_SECOND_HOUSE = {
    const.ARIES: const.PLUTO,
    const.SCORPIO: const.MARS,
    const.SAGITTARIUS: const.NEPTUNE,
    const.CAPRICORN: const.URANUS,
    const.AQUARIUS: const.SATURN,
    const.PISCES: const.JUPITER
}

ORBIT_NUM_TO_CHAR = {
    1: PLANET_TO_CHAR[const.MERCURY],
    2: PLANET_TO_CHAR[const.VENUS],
    3: PLANET_TO_CHAR[const.MARS],
    4: PLANET_TO_CHAR[const.JUPITER],
    5: PLANET_TO_CHAR[const.SATURN],
    6: PLANET_TO_CHAR[const.URANUS],
    7: PLANET_TO_CHAR[const.NEPTUNE],
    8: PLANET_TO_CHAR[const.PLUTO],
    9: PLANET_TO_CHAR[const.MOON]
}

ORBIT_LABELS = [const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN,
                const.URANUS, const.NEPTUNE, const.PLUTO, const.MOON]

PLANET_POWER = {
    const.ARIES: [[const.VENUS], [const.SATURN], [const.MERCURY, const.URANUS], [const.MOON],
                  [const.JUPITER, const.NEPTUNE], [const.SUN], [const.MARS, const.PLUTO]],
    const.TAURUS: [[const.MARS, const.PLUTO], [const.URANUS], [const.JUPITER, const.NEPTUNE], [const.SUN],
                   [const.SATURN, const.MERCURY], [const.MOON], [const.VENUS]],
    const.GEMINI: [[const.JUPITER, const.NEPTUNE], [const.CHIRON], [const.PLUTO, const.SUN, const.MARS], [const.MOON],
                   [const.SATURN, const.URANUS, const.VENUS], [const.MERCURY], [const.MERCURY]],
    const.CANCER: [[const.SATURN, const.URANUS], [const.MARS], [const.MERCURY, const.VENUS], [const.SUN],
                   [const.PLUTO, const.NEPTUNE], [const.JUPITER], [const.MOON]],
    const.LEO: [[const.SATURN, const.URANUS], [const.NEPTUNE], [const.VENUS, const.MERCURY], [const.MOON],
                [const.MARS, const.JUPITER], [const.PLUTO], [const.SUN]],
    const.VIRGO: [[const.JUPITER, const.NEPTUNE], [const.VENUS], [const.MOON, const.PLUTO, const.MARS], [const.SUN],
                  [const.SATURN, const.URANUS], [const.MERCURY], [const.MERCURY]],
    const.LIBRA: [[const.MARS, const.PLUTO], [const.SUN], [const.JUPITER, const.NEPTUNE], [const.MOON],
                  [const.MERCURY, const.URANUS], [const.SATURN], [const.VENUS]],
    const.SCORPIO: [[const.VENUS], [const.MOON], [const.SATURN, const.MERCURY], [const.SUN],
                    [const.JUPITER, const.NEPTUNE], [const.URANUS], [const.PLUTO, const.MARS]],
    const.SAGITTARIUS: [[const.MERCURY], [const.MERCURY], [const.SATURN, const.URANUS, const.VENUS], [const.MOON],
                        [const.SUN, const.MARS, const.PLUTO], [const.CHIRON], [const.JUPITER, const.NEPTUNE]],
    const.CAPRICORN: [[const.MOON], [const.JUPITER], [const.PLUTO, const.NEPTUNE], [const.SUN],
                      [const.MERCURY, const.VENUS], [const.MARS], [const.SATURN, const.URANUS]],
    const.AQUARIUS: [[const.SUN], [const.PLUTO], [const.JUPITER, const.MARS], [const.MOON],
                     [const.MERCURY, const.VENUS], [const.NEPTUNE], [const.URANUS, const.SATURN]],
    const.PISCES: [[const.MERCURY], [const.MERCURY], [const.SATURN, const.URANUS], [const.SUN],
                   [const.MOON, const.PLUTO, const.MARS], [const.VENUS], [const.NEPTUNE, const.JUPITER]]
}

NUMBER_TO_PLANET = {
    1: (const.SUN, (1, 0, 0)),
    2: (const.MOON, (1, 1, 1)),
    3: (const.JUPITER, (0, 1, 1)),
    4: (const.NORTH_NODE, (1, 1, 0)),
    5: (const.MERCURY, (0, 1, 0)),
    6: (const.VENUS, (1, 1, 1)),
    7: (const.SOUTH_NODE, (0.8, 0.8, 0.8)),
    8: (const.SATURN, (0, 0, 0)),
    9: (const.MARS, (1, 0, 0))
}


class SoulFormula:
    def __init__(self, dt: datetime, links: {str, str}, center: [[str]], orbits: {int: [str]},
                 retro: {str}, planet_power: {str: int}, additional_objects: {str: str}) -> None:
        self.dt = dt
        self.retro = retro
        self.orbits = orbits
        self.center = center
        self.links = links
        self.planet_power = planet_power
        self.additional_objects = additional_objects

        self.reverse_links = {}
        for from_planet, to_planet in links.items():
            planets = self.reverse_links.get(to_planet)
            if not planets:
                planets = []
                self.reverse_links[to_planet] = planets
            planets.append(from_planet)

        self.center_set = set()
        for center in self.center:
            for p in center:
                self.center_set.add(p)

        self.own_orbits = set()
        for orbit_num, planets in orbits.items():
            for planet in planets:
                if ORBIT_LABELS[orbit_num - 1] == planet:
                    self.own_orbits.add(planet)

    def __str__(self) -> str:
        res = self.dt.strftime('%Y-%m-%d %H:%M')
        res += '\n'
        for center in self.center:
            res += f'Ц: ' + ' '.join([self.__planet_as_str(p) for p in center])
            res += '\n'
        orbit_num = 1
        orbit = self.orbits.get(orbit_num, [])
        while len(orbit) > 0:
            res += f'{ORBIT_NUM_TO_CHAR[orbit_num]}: ' + ', '.join([self.__planet_as_str(p) for p in orbit])
            res += '\n'
            orbit_num += 1
            orbit = self.orbits.get(orbit_num, [])
        return res

    def __planet_as_str(self, planet):
        res = self.__planet_to_char(planet)
        support = ''.join([self.__planet_to_char(a) for a in self.reverse_links.get(planet, [])
                           if a != planet and a not in self.center_set])
        if support:
            res += f'(←{support})'
        return res

    def __planet_to_char(self, planet):
        p_char = PLANET_TO_CHAR[planet]
        if planet in self.retro:
            return p_char + 'ⸯ'
        return p_char

    def get_id(self):
        res = []
        for planet in [const.SUN, const.MOON,
                       const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN,
                       const.URANUS, const.NEPTUNE, const.PLUTO]:
            res.append(self.__planet_to_char(planet) + self.__planet_to_char(self.links[planet]))
        for planet in [const.CHIRON, const.NORTH_NODE, 'Lilith', 'Selena']:
            res.append(self.__planet_to_char(planet) + self.__planet_to_char(self.additional_objects[planet]))
        return '|'.join(res)

    def get_patterns(self):
        res = []
        for planet in self.center_set:
            res.append(f'0{self.__planet_to_char(planet)}')
        for num, planets in self.orbits.items():
            for planet in planets:
                res.append(f'{num}{self.__planet_to_char(planet)}')

        for planet in [const.SUN, const.MOON,
                       const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN,
                       const.URANUS, const.NEPTUNE, const.PLUTO]:
            res.append(self.__planet_to_char(planet) + self.__planet_to_char(self.links[planet]))
        return res

    def copy(self):
        return SoulFormula(
            self.dt,
            self.links.copy(),
            [a.copy() for a in self.center],
            self.orbits.copy(),
            self.retro.copy(),
            self.planet_power.copy(),
            self.additional_objects. copy()
        )


class SoulFormulaWithBorders:

    def __init__(self, formula: SoulFormula, from_dt: datetime, to_dt: datetime) -> None:
        self.to_dt = to_dt
        self.from_dt = from_dt
        self.formula = formula


class CosmogramPlanet:

    def __init__(self, name: str, lon: float, lat: float, sign: str, signlon: float,
                 movement: str, power: int) -> None:
        self.name = name
        self.movement = movement
        self.signlon = signlon
        self.sign = sign
        self.lat = lat
        self.lon = lon
        self.power = power

    def __str__(self) -> str:
        return f'{self.name}: {self.signlon} {self.sign} {self.lon}'

    def __repr__(self) -> str:
        return self.__str__()


class Cosmogram:

    def __init__(self, dt: datetime, planets: [CosmogramPlanet],
                 additional_planets: [CosmogramPlanet], death_dt: datetime = None, cur_time: datetime = None) -> None:
        self.additional_planets = additional_planets
        self.dt = dt
        self.cur_time = datetime.now(pytz.timezone("Europe/Moscow")) if cur_time is None else cur_time
        self.death_dt = death_dt
        self.planet_to_cosmogram_info = {}
        self.sign_to_planet = {}
        for planet in (planets + additional_planets):
            self.planet_to_cosmogram_info[planet.name] = planet
            pp = self.sign_to_planet.get(planet.sign)
            if pp is None:
                pp = []
                self.sign_to_planet[planet.sign] = pp
            pp.append(planet)

        self._calc_aspects()

    def get_planet_info(self, planet: str):
        result = self.planet_to_cosmogram_info.get(planet)
        if result is None:
            for p in self.additional_planets:
                if p.name == planet:
                    return p
        return result

    def get_planets_in_sign(self, sign: str) -> [CosmogramPlanet]:
        return self.sign_to_planet.get(sign, [])

    def get_planets(self) -> [CosmogramPlanet]:
        return self.planet_to_cosmogram_info.values()

    def get_max_planets_in_sign(self):
        return max(len(a) for a in self.sign_to_planet.values())

    def get_life_years(self):
        if self.death_dt:
            return self._get_year_diff(self.death_dt, self.dt)
        return self._get_year_diff(self.cur_time, self.dt)

    def get_life_days(self):
        if self.death_dt:
            return (self.death_dt - self.dt).days
        return (self.cur_time - self.dt).days

    def get_life_point_lon(self):
        if self.death_dt is None:
            return self._get_point_lon(self.cur_time, self.dt)
        return None

    def get_life_point_lon_on_date(self, dt: datetime):
        if self.death_dt is None:
            return self._get_point_lon(dt, self.dt)
        return None

    def get_death_point_lon(self):
        if self.death_dt is not None:
            return self._get_point_lon(self.death_dt, self.dt)
        return None

    def _calc_aspects(self):
        all_planets = [const.SUN, const.MOON,
                       const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN,
                       const.URANUS, const.NEPTUNE, const.PLUTO, const.CHIRON, const.NORTH_NODE, 'Lilith', 'Selena']
        planet_to_aspect = {}
        aspects = []
        for i in range(len(all_planets)):
            p1 = self.planet_to_cosmogram_info[all_planets[i]]
            for j in range(i + 1, len(all_planets)):
                p2 = self.planet_to_cosmogram_info[all_planets[j]]

                for aspect in MAJOR_ASPECTS:
                    p_diff = abs(p2.lon - p1.lon)
                    p_diff = min(360 - p_diff, p_diff)
                    diff = abs(p_diff - aspect)
                    if diff <= 1:
                    # if diff <= 2 or \
                    #         diff <= 10 and all_planets[i] in [const.SUN, const.MOON] or \
                    #         diff <= 10 and all_planets[j] in [const.SUN, const.MOON] or \
                    #         diff <= 5 and all_planets[i] not in [const.CHIRON, const.NORTH_NODE, 'Lilith', 'Selena'] or \
                    #         diff <= 5 and all_planets[j] not in [const.CHIRON, const.NORTH_NODE, 'Lilith', 'Selena']:
                        res1 = planet_to_aspect.get(all_planets[i], [])
                        res2 = planet_to_aspect.get(all_planets[j], [])
                        if len(res1) == 0:
                            planet_to_aspect[all_planets[i]] = res1
                        if len(res2) == 0:
                            planet_to_aspect[all_planets[j]] = res2
                        res1.append((all_planets[j], aspect))
                        res2.append((all_planets[i], aspect))
                        if aspect not in aspects:
                            aspects.append(aspect)
            self.planet_to_aspect = planet_to_aspect
            self.aspects = sorted(aspects)

    @staticmethod
    def _get_year_diff(cur_time, dt):
        year_diff = cur_time.year - dt.year

        prev_birthday = dt.replace(year=cur_time.year)
        if prev_birthday > cur_time:
            year_diff -= 1
        return year_diff

    def _get_point_lon(self, cur_time, dt):

        if dt > cur_time:
            return None
        # if cur_time.year - dt.year > 84:
        #     y_cnt = (cur_time.year - dt.year) // 84
        #     dt = dt.replace(year=dt.year + 84 * y_cnt)
        year_diff = self._get_year_diff(cur_time, dt)

        prev_birthday = dt.replace(year=cur_time.year)
        next_birthday = dt.replace(year=cur_time.year + 1)
        if prev_birthday > cur_time:
            next_birthday = prev_birthday
            prev_birthday = prev_birthday.replace(year=prev_birthday.year - 1)
        cur_year_len_in_days = (next_birthday - prev_birthday).days
        cur_year_lon = ((cur_time - prev_birthday).days / cur_year_len_in_days) * (360 / 84)
        result_lon = year_diff * (360 / 84) + cur_year_lon
        return result_lon

    def __str__(self) -> str:
        s = self.dt.strftime('%Y-%m-%d %H:%M') + '\n'
        for planet, info in self.planet_to_cosmogram_info.items():
            s += str(info) + '\n'
        return s

    def __repr__(self) -> str:
        return self.__str__()


class NumericInfo:

    def __init__(self, dt: datetime) -> None:
        self.soul_number = self._get_num(dt.strftime('%d'))
        self.fate_number = self._get_num(dt.strftime('%Y%m%d'))

    def _get_num(self, s: str):
        sum = 0
        for digit in s:
            sum += int(digit)
        if sum >= 10:
            return self._get_num(str(sum))
        return sum


class SoulFormulaBuilder:
    @abstractmethod
    def build_formula(self, dt: datetime, lat, lon) -> SoulFormula:
        pass

    @abstractmethod
    def build_cosmogram(self, dt: datetime, lat, lon) -> Cosmogram:
        pass


if __name__ == '__main__':
    formula1 = SoulFormula(
        dt=datetime.strptime('1987-02-04 13:08', '%Y-%m-%d %H:%M'),
        links={
            const.SUN: const.SUN,
            const.MOON: const.URANUS,
            const.MERCURY: const.SUN,
            const.VENUS: const.MERCURY,
            const.MARS: const.MOON,
            const.JUPITER: const.VENUS,
            const.SATURN: const.MARS,
            const.URANUS: const.JUPITER,
            const.NEPTUNE: const.SATURN,
            const.PLUTO: const.NEPTUNE
        },
        center=[
            [const.SUN]
        ],
        orbits={
            1: [const.MERCURY],
            2: [const.VENUS],
            3: [const.JUPITER],
            4: [const.URANUS],
            5: [const.MOON],
            6: [const.MARS],
            7: [const.SATURN],
            8: [const.NEPTUNE],
            9: [const.PLUTO]
        },
        retro={const.URANUS, const.SATURN, const.NEPTUNE, const.PLUTO},
        planet_power={
            const.SUN: 6,
            const.MOON: 0,
            const.MERCURY: 1,
            const.VENUS: 4,
            const.MARS: 3,
            const.JUPITER: 2,
            const.SATURN: 6,
            const.URANUS: 6,
            const.NEPTUNE: 6,
            const.PLUTO: 5
        }
    )
    formula2 = SoulFormula(
        dt=datetime.strptime('1987-02-04 13:08', '%Y-%m-%d %H:%M'),
        links={
            const.SUN: const.VENUS,
            const.MOON: const.VENUS,
            const.MERCURY: const.MERCURY,
            const.VENUS: const.MOON,
            const.MARS: const.URANUS,
            const.JUPITER: const.SUN,
            const.SATURN: const.PLUTO,
            const.URANUS: const.MOON,
            const.NEPTUNE: const.VENUS,
            const.PLUTO: const.SUN
        },
        center=[
            [const.VENUS, const.MOON],
            [const.MERCURY]
        ],
        orbits={
            1: [const.SUN, const.NEPTUNE, const.URANUS],
            2: [const.PLUTO, const.JUPITER, const.MARS],
            3: [const.SATURN]
        },
        retro={const.MERCURY, const.SATURN, const.NEPTUNE},
        planet_power={
            const.SUN: 6,
            const.MOON: 0,
            const.MERCURY: 1,
            const.VENUS: 4,
            const.MARS: 3,
            const.JUPITER: 2,
            const.SATURN: 6,
            const.URANUS: 6,
            const.NEPTUNE: 6,
            const.PLUTO: 5
        },
        additional_objects=[]
    )
    print(formula1)
    print(formula2)
