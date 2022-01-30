import configparser
import time
from datetime import datetime, timedelta

import pytz
from flatlib import const

from ext.sf_geocoder import DefaultSFGeocoder
from model.sf import Cosmogram
from model.sf_flatlib import FlatlibBuilder


def build_transit(cosmogram: Cosmogram, planet_to_transit: str,
                  start_date: datetime, end_date: datetime):
    builder = FlatlibBuilder()
    dt = start_date
    cosmogram_cur = builder.build_cosmogram(dt)
    start_lon = cosmogram_cur.get_planet_info(planet_to_transit).lon
    cur_lon = start_lon
    print(cur_lon)

    days_cnt = 0
    # while start_lon <= cur_lon or abs(cur_lon - start_lon) > 1 or days_cnt < 350 * 20:
    while dt < end_date:
        dt += timedelta(hours=6)
        cosmogram_cur = builder.build_cosmogram(dt)
        cur_lon = cosmogram_cur.get_planet_info(planet_to_transit).lon
        days_cnt += 0.25
        pl = ''
        for planet in [const.SUN, const.MOON,
                       const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN,
                       const.URANUS, const.NEPTUNE, const.PLUTO, const.CHIRON, const.NORTH_NODE,
                       'Lilith', 'Selena', const.PARS_FORTUNA]:
            planet_info = cosmogram.get_planet_info(planet)
            if abs(planet_info.lon - cur_lon) < 0.1:
                pl = planet_info.name + ' ' + str(round(cur_lon - planet_info.lon, 1))

                dt_str = dt.strftime('%d.%m.%Y')
                print(days_cnt, round(cur_lon, 1), cosmogram_cur.get_planet_info(planet_to_transit).movement, pl,
                      dt_str)
        # dt_str = ''
        # if pl:
        #     dt_str = dt.strftime('%d.%m.%Y')
        #
        # print(days_cnt, round(cur_lon, 1), cosmogram_cur.get_planet_info(planet_to_transit).movement, pl, dt_str)


def get_discrete_value(lon: float) -> int:
    res = round(lon)
    if res >= 360:
        return 360 - res
    if res < 0:
        return 360 + res
    return res


def find_nearest_connections(cosmo: Cosmogram, from_date: datetime) -> {str, (str, datetime)}:
    all_planets = [const.SUN, const.MOON,
                   const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN,
                   const.URANUS, const.NEPTUNE, const.PLUTO, const.CHIRON, const.NORTH_NODE,
                   'Lilith', 'Selena']

    discrete_lon_to_planets = {}
    for planet in all_planets:
        discrete_lon = get_discrete_value(cosmo.get_planet_info(planet).lon)
        planets = discrete_lon_to_planets.get(discrete_lon, [])
        if len(planets) == 0:
            discrete_lon_to_planets[discrete_lon] = planets
        # название планеты; направление (1 — прямое, -1 — ретроградное, 0 — уже в соединении); кол-во шагов до планеты
        planets.append((planet, 0, 0))

    for i in range(360):
        discrete_lon = get_discrete_value(i)
        planets = discrete_lon_to_planets.get(discrete_lon, [])
        if len(planets) > 0:
            continue
        discrete_lon_to_planets[discrete_lon] = planets
        k = i
        ln = 0
        while True:
            k += 1
            ln += 1
            if k == 360:
                k = 0

            dv = get_discrete_value(k)
            next_planets = [a for a in discrete_lon_to_planets.get(dv, []) if a[1] == 0]
            if len(next_planets) > 0:
                planets.append((next_planets[0][0], 1, ln))
                break
        k = i
        ln = 0
        while True:
            k -= 1
            ln += 1
            if k == -1:
                k = 359

            dv = get_discrete_value(k)
            next_planets = [a for a in discrete_lon_to_planets.get(dv, []) if a[1] == 0]
            if len(next_planets) > 0:
                planets.append((next_planets[0][0], -1, ln))
                break

    builder = FlatlibBuilder()
    result = {}
    for planet in all_planets:
        transit_cosmo = builder.build_cosmogram(from_date)
        planet_discrete_lon = get_discrete_value(transit_cosmo.get_planet_info(planet).lon)
        max_step = min([a[2] for a in discrete_lon_to_planets.get(planet_discrete_lon)])
        td = _get_big_timedelta(planet)
        dt = from_date + td + td * max(max_step - 2, 0)
        p, pdt = find_connection(cosmo, planet, dt)
        result[planet] = (p, pdt)
    return result


def find_connection(cosmo: Cosmogram, planet_to_search: str, from_date: datetime) -> (str, datetime):
    builder = FlatlibBuilder()
    dt = from_date
    while True:
        transit_cosmo = builder.build_cosmogram(dt)
        pl1 = transit_cosmo.get_planet_info(planet_to_search).lon
        min_planet, min_angle = None, 360
        for planet in [const.SUN, const.MOON,
                       const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN,
                       const.URANUS, const.NEPTUNE, const.PLUTO, const.CHIRON, const.NORTH_NODE,
                       'Lilith', 'Selena']:
            pl2 = cosmo.get_planet_info(planet).lon
            p_diff = abs(pl1 - pl2)
            p_diff = min(360 - p_diff, p_diff)
            if min_angle > p_diff:
                min_angle = p_diff
                min_planet = planet
        if min_angle < 1:
            return min_planet, find_zero_conneсtion(cosmo, planet_to_search, min_planet, dt)
        dt += _get_big_timedelta(planet_to_search)


def _get_big_timedelta(planet: str) -> timedelta:
    if planet in [const.MOON]:
        return timedelta(hours=2)
    if planet in [const.MERCURY]:
        return timedelta(hours=6)
    if planet in [const.VENUS]:
        return timedelta(hours=15)
    if planet in [const.SUN]:
        return timedelta(days=1)
    if planet in [const.MARS]:
        return timedelta(days=2)
    if planet in ['Selena']:
        return timedelta(days=7)
    if planet in ['Lilith']:
        return timedelta(days=9)
    if planet in [const.JUPITER]:
        return timedelta(days=12)
    if planet in [const.NORTH_NODE]:
        return timedelta(days=19)
    if planet in [const.SATURN]:
        return timedelta(days=30)
    if planet in [const.CHIRON]:
        return timedelta(days=51)
    if planet in [const.URANUS]:
        return timedelta(days=85)
    if planet in [const.NEPTUNE]:
        return timedelta(days=166)
    if planet in [const.PLUTO]:
        return timedelta(days=251)
    raise ValueError(f'Неизвестная планета => {planet}')


def _get_small_timedelta(planet: str) -> timedelta:
    if planet in [const.MOON, const.SUN, const.MERCURY, const.VENUS, const.MARS]:
        return timedelta(hours=1)
    if planet in [const.JUPITER, const.SATURN, const.CHIRON, const.NORTH_NODE, 'Lilith', 'Selena']:
        return timedelta(days=1)
    if planet in [const.URANUS, const.NEPTUNE, const.PLUTO]:
        return timedelta(days=30)
    raise ValueError(f'Неизвестная планета => {planet}')


def find_zero_conneсtion(cosmo: Cosmogram, planet_to_search: str, dest_planet: str, from_date: datetime) -> (
        str, datetime):
    builder = FlatlibBuilder()
    pl1 = cosmo.get_planet_info(dest_planet).lon

    td = _get_small_timedelta(planet_to_search)

    left = from_date + td
    right = from_date - td
    cosmo_l = builder.build_cosmogram(left)
    cosmo_r = builder.build_cosmogram(right)
    pll = cosmo_l.get_planet_info(planet_to_search).lon
    plr = cosmo_r.get_planet_info(planet_to_search).lon

    p_diffl = abs(pl1 - pll)
    p_diffl = min(360 - p_diffl, p_diffl)

    p_diffr = abs(pl1 - plr)
    p_diffr = min(360 - p_diffr, p_diffr)

    if p_diffl < p_diffr:
        k = 1
        p_diff = p_diffl
        prev_diff = p_diffr
        dt = left
    else:
        k = -1
        p_diff = p_diffr
        prev_diff = p_diffl
        dt = right

    while prev_diff > p_diff:
        dt += k * td
        cosmo_t = builder.build_cosmogram(dt)
        prev_diff = p_diff
        l = cosmo_t.get_planet_info(planet_to_search).lon
        p_diff = abs(pl1 - l)
        p_diff = min(360 - p_diff, p_diff)
    return dt - k * td


if __name__ == '__main__':
    config = configparser.RawConfigParser()
    config.read('../sf_config.ini')
    config.read('../sf_config_local.ini')

    geocoder = DefaultSFGeocoder(config.get('Geocoder', 'token'))

    birthday_time = '1987-01-10 12:00'
    geo_res = geocoder.get_geo_position('Тобольск', birthday_time)
    # print(geo_res)

    # birthday_time = '1991-08-20 16:51'
    # geo_res = get_geo_position('Москва', birthday_time)

    # birthday_time = '1992-03-19 12:00'
    # geo_res = get_geo_position('Омск', birthday_time)
    # print(geo_res)

    builder = FlatlibBuilder()

    dt = datetime.strptime(f'{birthday_time} {geo_res.utc_offset}', '%Y-%m-%d %H:%M %z')
    cosmogram = builder.build_cosmogram(dt, lat=geo_res.lat, lon=geo_res.lon)

    cur_dt = datetime.now(pytz.timezone("Europe/Moscow"))
    cur_dt = cur_dt.replace(hour=0, minute=1)
    # end_dt = datetime.now(pytz.timezone("Europe/Moscow"))
    # end_dt = end_dt.replace(year=2015)
    # build_transit(cosmogram, const.MARS, cur_dt, end_dt)
    # build_transit(cosmogram, const.MOON, cur_dt, end_dt)

    ts0 = time.time()
    planet_to_nearest_connection = find_nearest_connections(cosmogram, cur_dt)
    print(f'Общее время нового алгоритма {round(time.time() - ts0, 1)} сек')

    ts = time.time()
    for p in [const.SUN, const.MOON,
              const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN,
              const.URANUS, const.NEPTUNE, const.PLUTO, const.CHIRON, const.NORTH_NODE,
              'Lilith', 'Selena']:
        t1 = time.time()
        planet, dt = find_connection(cosmogram, p, cur_dt)
        tdiff = time.time() - t1
        print(f'{p} <-> {planet} ({round(tdiff, 1)} cек)')
        print(dt.strftime('%d.%m.%Y %H:%M'))
        planet1, dt1 = planet_to_nearest_connection.get(p)
        print(dt1.strftime('%d.%m.%Y %H:%M') + ' ' + planet1)
        print()
    print(f'Общее время {round(time.time() - ts, 1)} сек')
