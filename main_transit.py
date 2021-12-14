import os
from pathlib import Path
from flatlib import const

import cairo

from datetime import datetime, timedelta

from transliterate import translit

from ext.sf_geocoder import get_geo_position
from model.sf_flatlib import FlatlibBuilder
from utils.sf_csv import read_csv_file
from view.sf_cosmogram import DefaultCosmogramDrawer


def draw_transit(name, birthday_time, city, dt_from: datetime, dt_to: datetime):
    name_tr = translit(name, "ru", reversed=True)
    name_tr = name_tr.replace(' ', '_').replace('\'', '').lower()

    geo_res = get_geo_position(city, birthday_time)
    print(f'UTC => {geo_res}')

    dir_name = f'pic/{name_tr}_transit'
    Path(dir_name).mkdir(parents=True, exist_ok=True)

    dt_birthday = datetime.strptime(f'{birthday_time} {geo_res.utc_offset}', '%Y-%m-%d %H:%M %z')
    builder = FlatlibBuilder()
    cosmo1 = builder.build_cosmogram(dt_birthday, lat=geo_res.lat, lon=geo_res.lon,
                                     planets_to_exclude=[const.PARS_FORTUNA])

    dt = dt_from
    while dt <= dt_to:
        surface_pdf = cairo.PDFSurface(f"{dir_name}/{name_tr}_{dt.strftime('%Y-%m-%d')}.pdf", 200, 200)
        cr = cairo.Context(surface_pdf)
        cr.scale(200, 200)

        cosmo2 = builder.build_cosmogram(dt, planets_to_exclude=[const.PARS_FORTUNA])

        drawer = DefaultCosmogramDrawer(planet_ruler_place='in_sign', life_years=0)
        drawer.draw_transit(cosmo1, cosmo2, cr)
        surface_pdf.finish()

        dt += timedelta(days=1)


if __name__ == '__main__':

    dt_from = datetime.strptime('2021-12-17 12:00 +0300', '%Y-%m-%d %H:%M %z')
    dt_to = datetime.strptime('2022-12-31 12:00 +0300', '%Y-%m-%d %H:%M %z')

    row = read_csv_file('in_data/user_info.csv')[-1]

    name = row['name']
    birthday = row['birthday']
    city = row['city']

    draw_transit(name, birthday, city, dt_from, dt_to)
