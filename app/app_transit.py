import os
import tempfile
from flatlib import const

import cairo

from datetime import datetime

from ext.sf_geocoder import SFGeocoder
from model.sf_flatlib import FlatlibBuilder
from view.sf_cosmogram import DefaultCosmogramDrawer


def generate_full_transit(geocoder, birthday_time, city, dt: datetime, cur_city,
                          show_source: bool, show_source_to_transit: bool, show_transit: bool):
    birthday_as_str = birthday_time.strftime('%Y-%m-%d %H:%M')
    dt_as_str = dt.strftime('%Y-%m-%d %H:%M')

    geo_res = geocoder.get_geo_position(city, birthday_as_str)
    geo_res_now = geocoder.get_geo_position(cur_city, dt_as_str)

    dt_birthday = datetime.strptime(f'{birthday_as_str} {geo_res.utc_offset}', '%Y-%m-%d %H:%M %z')
    dt_transit = datetime.strptime(f'{dt_as_str} {geo_res_now.utc_offset}', '%Y-%m-%d %H:%M %z')
    builder = FlatlibBuilder()
    cosmo1 = builder.build_cosmogram(dt_birthday, lat=geo_res.lat, lon=geo_res.lon,
                                     planets_to_exclude=[const.PARS_FORTUNA])

    new_file, filename = tempfile.mkstemp(suffix='.pdf', prefix='transit_')
    print(f'Создан временный файл для вывода космограммы: {filename}')
    surface_pdf = cairo.PDFSurface(filename, 200, 200)
    cr = cairo.Context(surface_pdf)
    cr.scale(200, 200)

    cosmo2 = builder.build_cosmogram(dt_transit, lat=geo_res_now.lat, lon=geo_res_now.lon,
                                     planets_to_exclude=[const.PARS_FORTUNA])

    drawer = DefaultCosmogramDrawer(planet_ruler_place='in_sign', life_years=0)
    drawer.draw_transit(cosmo1, cosmo2, cr, show_source, show_source_to_transit, show_transit)
    surface_pdf.finish()
    os.close(new_file)

    return filename


def generate_transit(geocoder: SFGeocoder, birthday_time: datetime, city, dt: datetime, cur_city: str,
                     show_source: bool, show_source_to_transit: bool, show_transit: bool) -> str:
    birthday_as_str = birthday_time.strftime('%Y-%m-%d %H:%M')
    dt_as_str = dt.strftime('%Y-%m-%d %H:%M')

    geo_res = geocoder.get_geo_position(city, birthday_as_str)
    geo_res_now = geocoder.get_geo_position(cur_city, dt_as_str)

    dt_birthday = datetime.strptime(f'{birthday_as_str} {geo_res.utc_offset}', '%Y-%m-%d %H:%M %z')
    dt_transit = datetime.strptime(f'{dt_as_str} {geo_res_now.utc_offset}', '%Y-%m-%d %H:%M %z')

    builder = FlatlibBuilder()
    cosmo1 = builder.build_cosmogram(dt_birthday, lat=geo_res.lat, lon=geo_res.lon,
                                     planets_to_exclude=[const.PARS_FORTUNA])

    new_file, filename = tempfile.mkstemp(suffix='.png', prefix='transit_')
    print(f'Создан временный файл для вывода космограммы: {filename}')
    w, h = 2000, 2000
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cr = cairo.Context(surface)
    cr.scale(w, h)

    cosmo2 = builder.build_cosmogram(dt_transit, lat=geo_res_now.lat, lon=geo_res_now.lon,
                                     planets_to_exclude=[const.PARS_FORTUNA])

    drawer = DefaultCosmogramDrawer(planet_ruler_place='in_sign', life_years=0)
    drawer.draw_transit(cosmo1, cosmo2, cr, show_source, show_source_to_transit, show_transit)
    surface.write_to_png(filename)
    surface.finish()
    os.close(new_file)

    return filename
