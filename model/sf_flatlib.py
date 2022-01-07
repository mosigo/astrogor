import configparser
from datetime import datetime, timedelta

import swisseph
from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

from ext.sf_geocoder import DefaultSFGeocoder
from model.sf import SoulFormula, SIGN_TO_HOUSE, SoulFormulaBuilder, PLANET_POWER, Cosmogram, CosmogramPlanet


class FlatlibBuilder(SoulFormulaBuilder):

    def build_cosmogram(self, dt: datetime, lat=55.75322, lon=37.622513,
                        death_dt: datetime = None, planets_to_exclude=None, cur_time=None) -> Cosmogram:
        date = self.__dt_to_flatlib_dt(dt)
        pos = GeoPos(lat, lon)
        swisseph.set_ephe_path('/usr/local/share/ephe')
        chart = Chart(date, pos, IDs=const.LIST_OBJECTS)

        all_planets = [const.SUN, const.MOON,
                       const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN,
                       const.URANUS, const.NEPTUNE, const.PLUTO]
        planet_infos = []
        for planet in all_planets:
            if planets_to_exclude and planet in planets_to_exclude:
                continue
            obj = chart.getObject(planet)
            power = self.__get_planet_power(planet, obj.sign)
            planet_infos.append(
                CosmogramPlanet(planet, obj.lon, obj.lat, obj.sign, obj.signlon,
                                obj.movement(), power)
            )

        additional_planets = []
        for additional_planet in [const.CHIRON, const.NORTH_NODE, const.PARS_FORTUNA]:
            if planets_to_exclude and additional_planet in planets_to_exclude:
                continue
            obj = chart.getObject(additional_planet)
            power = 0
            additional_planets.append(
                CosmogramPlanet(additional_planet, obj.lon, obj.lat, obj.sign, obj.signlon,
                                obj.movement(), power)
            )
        if not planets_to_exclude or 'Lilith' not in planets_to_exclude:
            lilith = self.__get_lilith(dt, 12)
            additional_planets.append(
                CosmogramPlanet('Lilith', lilith['lon'], lilith['lat'], lilith['sign'], lilith['signlon'], const.DIRECT, 0)
            )
        if not planets_to_exclude or 'Selena' not in planets_to_exclude:
            selena = self.__get_lilith(dt, 56)
            additional_planets.append(
                CosmogramPlanet('Selena', selena['lon'], selena['lat'], selena['sign'], selena['signlon'], const.DIRECT, 0)
            )

        return Cosmogram(dt, planet_infos, additional_planets, death_dt, cur_time)

    def build_formula(self, dt: datetime, lat=55.75322, lon=37.622513) -> SoulFormula:
        date = self.__dt_to_flatlib_dt(dt)
        pos = GeoPos(lat, lon)
        swisseph.set_ephe_path('/usr/local/share/ephe')
        chart = Chart(date, pos, IDs=const.LIST_OBJECTS)

        f = self.__chart_to_formula(dt, chart)
        lilith = self.__get_lilith(dt, 12)
        selena = self.__get_lilith(dt, 56)
        f.additional_objects['Lilith'] = SIGN_TO_HOUSE[lilith['sign']]
        f.additional_objects['Selena'] = SIGN_TO_HOUSE[selena['sign']]
        return f

    def __get_lilith(self, dt: datetime, id: int):
        jd = self.__dt_to_flatlib_dt(dt).jd
        sweList, _ = swisseph.calc_ut(jd, id)
        lon = sweList[0]
        return {
            'id': 'Lilith',
            'lon': lon,
            'lat': sweList[1],
            'lonspeed': sweList[3],
            'latspeed': sweList[4],
            'sign': const.LIST_SIGNS[int(lon / 30)],
            'signlon': lon % 30
        }

    @staticmethod
    def __dt_to_flatlib_dt(dt: datetime):
        # return Datetime(dt.strftime('%Y/%m/%d'), dt.strftime('%H:%M'), '+03:00')
        offset = dt.strftime('%z')
        if not offset:
            offset = '+00:00'
        else:
            offset = offset[:3] + ':' + offset[3:5]
        return Datetime(dt.strftime('%Y/%m/%d'), dt.strftime('%H:%M'), offset)

    @staticmethod
    def __get_planet_power(planet, planet_sign):
        planet_power = PLANET_POWER[planet_sign]
        i = 6
        while i >= 0:
            if planet in planet_power[i]:
                return i
            i -= 1
        raise ValueError(f'Не нашлась сила планеты для {planet} в {planet_sign}.')

    def __chart_to_formula(self, dt: datetime, chart: Chart) -> SoulFormula:
        # dt = datetime.strptime(str(chart.date)[1:17], '%Y/%m/%d %H:%M')
        retro = set()
        links = {}
        center = []
        orbits = {}
        power = {}

        houses = set()
        center_planes = set()

        all_planets = [const.SUN, const.MOON,
                       const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN,
                       const.URANUS, const.NEPTUNE, const.PLUTO]
        for planet in all_planets:
            planet_obj = chart.getObject(planet)

            if planet_obj.movement() == const.RETROGRADE:
                retro.add(planet)

            house = SIGN_TO_HOUSE[planet_obj.sign]
            links[planet] = house

            houses.add(house)

            power[planet] = self.__get_planet_power(planet, planet_obj.sign)

        additional_objects = {}
        for additional_planet in [const.CHIRON, const.NORTH_NODE, const.PARS_FORTUNA]:
            obj = chart.getObject(additional_planet)
            additional_objects[additional_planet] = SIGN_TO_HOUSE[obj.sign]
            if obj.movement() == const.RETROGRADE:
                retro.add(additional_planet)

        start_set = set(houses)
        while len(start_set) > 0:
            planet = start_set.pop()
            current_circle = []
            house = links[planet]
            current_circle.append(planet)
            while house not in current_circle:
                current_circle.append(house)
                house = links[house]
            if house == planet:
                current_circle.reverse()
                center.append(current_circle)
                for p in current_circle:
                    center_planes.add(p)
                    if p != planet:
                        start_set.remove(p)

        leaves = set(all_planets).difference(houses)
        for leave in leaves:
            chain = [leave]
            house = links[leave]
            while house not in center_planes:
                chain.append(house)
                house = links[house]
            chain.reverse()
            orbit_num = 1
            for planet in chain:
                orbit_planets = orbits.get(orbit_num)
                if not orbit_planets:
                    orbit_planets = []
                    orbits[orbit_num] = orbit_planets
                if planet not in orbit_planets:
                    orbit_planets.append(planet)
                orbit_num += 1

        return SoulFormula(dt, links, center, orbits, retro, power, additional_objects)


def get_borders(dt: datetime, lat: float, lon: float):
    builder = FlatlibBuilder()
    formula = builder.build_formula(dt, lat=lat, lon=lon)
    formula_id = formula.get_id()
    left = dt - timedelta(hours=1)
    left_formula = builder.build_formula(left, lat=lat, lon=lon)
    while left_formula.get_id() == formula_id:
        left -= timedelta(hours=1)
        left_formula = builder.build_formula(left, lat=lat, lon=lon)
    while left_formula.get_id() != formula_id:
        left += timedelta(minutes=1)
        left_formula = builder.build_formula(left, lat=lat, lon=lon)

    right = dt + timedelta(hours=1)
    right_formula = builder.build_formula(right, lat=lat, lon=lon)
    while right_formula.get_id() == formula_id:
        right += timedelta(hours=1)
        right_formula = builder.build_formula(right, lat=lat, lon=lon)
    while right_formula.get_id() != formula_id:
        right -= timedelta(minutes=1)
        right_formula = builder.build_formula(right, lat=lat, lon=lon)

    return left_formula.dt, right_formula.dt


if __name__ == '__main__':
    config = configparser.RawConfigParser()
    config.read('sf_config.ini')
    config.read('sf_config_local.ini')

    geocoder = DefaultSFGeocoder(config.get('Geocoder', 'token'))

    builder = FlatlibBuilder()
    geo_data = geocoder.get_geo_position('Тобольск')
    dt = datetime.strptime('1987-01-10 12:00 ' + geo_data.utc_offset, '%Y-%m-%d %H:%M %z')

    formula = builder.build_formula(
        dt,
        lat=geo_data.lat, lon=geo_data.lon
    )
    print(formula)
    print(formula.get_id())
    print(formula.get_patterns())
    print(formula.planet_power)
    print(formula.additional_objects)

    cosmogram = builder.build_cosmogram(
        dt,
        lat=geo_data.lat, lon=geo_data.lon
    )
    print(cosmogram)
