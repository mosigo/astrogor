from datetime import datetime, timedelta

import pytz
from flatlib import const

from model.sf import Cosmogram
from model.sf_flatlib import FlatlibBuilder


if __name__ == '__main__':
    builder = FlatlibBuilder()

    # cur_dt = datetime.now(pytz.timezone("Europe/Moscow")) + timedelta(days=6)
    cur_dt = datetime.now(pytz.timezone("Europe/Moscow"))
    cosmo = builder.build_cosmogram(cur_dt)

    sun_lon = cosmo.get_planet_info(const.SUN).lon
    moon_lon = cosmo.get_planet_info(const.MOON).lon
    print(f'sun={sun_lon}, moon={moon_lon}')
    if moon_lon > sun_lon:
        diff = moon_lon - sun_lon
    else:
        if sun_lon - moon_lon >= 180:
            diff = sun_lon - moon_lon - 180
        else:
            diff = 360 - (sun_lon - moon_lon)
    moon_diff_in_minutes = (28 * 24 * 60) * diff / 360
    sun_diff_in_gradus = 360 * moon_diff_in_minutes / (365 * 24 * 60)
    print(f'солнце прошло {sun_diff_in_gradus} градусов')
    sun_diff_in_minutes = (28 * 24 * 60) * sun_diff_in_gradus / 360
    print(f'луна прошла {sun_diff_in_gradus} градусов за {sun_diff_in_minutes} минут')
    print(f'diff={diff}, minutes={moon_diff_in_minutes}, hours={moon_diff_in_minutes / 60}, days={moon_diff_in_minutes / 60 / 24}')
    first_day_of_lunar_month = cur_dt - timedelta(minutes=int(moon_diff_in_minutes + sun_diff_in_minutes))
    print(f'first day of month = {first_day_of_lunar_month}')

    cosmo1 = builder.build_cosmogram(first_day_of_lunar_month)
    sun_lon1 = cosmo1.get_planet_info(const.SUN).lon
    moon_lon1 = cosmo1.get_planet_info(const.MOON).lon
    print(f'sun lon = {sun_lon1}, moon lon = {moon_lon1}')

    while abs(sun_lon1 - moon_lon1) > 0.005:
        first_day_of_lunar_month += timedelta(minutes=1)
        cosmo1 = builder.build_cosmogram(first_day_of_lunar_month)
        sun_lon1 = cosmo1.get_planet_info(const.SUN).lon
        moon_lon1 = cosmo1.get_planet_info(const.MOON).lon
        print(f'sun lon = {sun_lon1}, moon lon = {moon_lon1}')
    print(f'Дата: {cur_dt}')
    print(f'Первый лунный день: {first_day_of_lunar_month}')
    print(f'Градус старта 1-го дня: {moon_lon1}')
    print(f'Полных лунных дней прошло: {(cur_dt - first_day_of_lunar_month).days}')

    dt1 = datetime.strptime('2021-11-05 00:15 +03:00', '%Y-%m-%d %H:%M %z')
    dt2 = datetime.strptime('2021-12-04 10:43 +03:00', '%Y-%m-%d %H:%M %z')
    print((dt2 - dt1).total_seconds() / 60 / 60 / 24)





