from datetime import datetime, timedelta

import pytz
from flatlib import const

from ext.sf_geocoder import get_geo_position
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


if __name__ == '__main__':
    birthday_time = '1987-01-10 12:00'
    geo_res = get_geo_position('Тобольск', birthday_time)
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
    cur_dt = cur_dt.replace(hour=12, minute=0, year=2014)
    end_dt = datetime.now(pytz.timezone("Europe/Moscow"))
    end_dt = end_dt.replace(year=2015)
    build_transit(cosmogram, const.MARS, cur_dt, end_dt)
    # build_transit(cosmogram, const.MOON, cur_dt, end_dt)
