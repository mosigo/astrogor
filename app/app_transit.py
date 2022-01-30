import base64
import math
import os
import tempfile
from flatlib import const

import cairo

from datetime import datetime, timedelta

from ext.sf_geocoder import SFGeocoder
from model.sf_flatlib import FlatlibBuilder
from model.sf_transit import find_nearest_connections
from view.planet_label import PlanetLabelDrawer
from view.sf_cosmogram import DefaultCosmogramDrawer


def generate_full_transit(geocoder, birthday_time: datetime, city: str, dt: datetime, cur_city: str,
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


def generate_transit(geocoder: SFGeocoder, birthday_time: datetime, city: str, dt: datetime, cur_city: str,
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


def get_nearest_transit_connections(geocoder: SFGeocoder, birthday_time: datetime, city: str,
                                    dt: datetime, cur_city: str) -> {str, (str, datetime)}:
    birthday_as_str = birthday_time.strftime('%Y-%m-%d %H:%M')
    dt_as_str = dt.strftime('%Y-%m-%d %H:%M')

    geo_res = geocoder.get_geo_position(city, birthday_as_str)
    geo_res_now = geocoder.get_geo_position(cur_city, dt_as_str)

    dt_birthday = datetime.strptime(f'{birthday_as_str} {geo_res.utc_offset}', '%Y-%m-%d %H:%M %z')
    dt_transit = datetime.strptime(f'{dt_as_str} {geo_res_now.utc_offset}', '%Y-%m-%d %H:%M %z')

    builder = FlatlibBuilder()
    cosmo1 = builder.build_cosmogram(dt_birthday, lat=geo_res.lat, lon=geo_res.lon,
                                     planets_to_exclude=[const.PARS_FORTUNA])

    res = find_nearest_connections(cosmo1, (dt_transit + timedelta(days=1)).replace(hour=0, minute=1))
    view = {}
    for planet1, (planet2, _, movement1) in res.items():
        b64 = get_connection_pic(planet1, planet2,
                                 movement1 == const.RETROGRADE,
                                 cosmo1.get_planet_info(planet2).movement == const.RETROGRADE)
        view[planet1] = b64
    return res, view


def get_connection_pic(planet1: str, planet2: str, is_retro1: bool, is_retro2: bool) -> str:
    new_file, filename = tempfile.mkstemp(suffix='.png', prefix='transit_')
    h = 100
    w = h * 3
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cr = cairo.Context(surface)
    cr.scale(h, h)

    cr.set_line_width(0.02)
    cr.set_source_rgb(0, 0, 0)

    cr.move_to(1.0, 0.5)
    cr.line_to(2, 0.5)
    cr.stroke()
    cr.arc(1.5, 0.5, 0.1, 0, 2 * math.pi)
    cr.fill()
    cr.set_source_rgba(0, 0, 1, 0.5)
    cr.arc(1.5, 0.5, 0.3, 0, 2 * math.pi)
    cr.fill()

    space = 0.1

    cr.set_line_width(0.06)
    cr.set_source_rgb(0, 0, 0)
    if is_retro1:
        cr.set_source_rgb(1, 0, 0)

    drawer = PlanetLabelDrawer()

    cr.save()
    cr.translate(space, space)
    cr.scale(1 - space * 2, 1 - space * 2)
    drawer.draw_planet(planet1, cr)
    cr.restore()

    cr.translate(2, 0)

    space = 0.1
    cr.set_line_width(0.06)

    cr.set_source_rgba(0, 0, 0, 0.5)
    if is_retro2:
        cr.set_source_rgba(1, 0, 0, 0.5)

    cr.save()
    cr.translate(space, space)
    cr.scale(1 - space * 2, 1 - space * 2)
    drawer.draw_planet(planet2, cr)
    cr.restore()

    surface.write_to_png(filename)
    surface.finish()
    os.close(new_file)

    with open(filename, "rb") as img_file:
        b64_string = base64.b64encode(img_file.read()).decode('utf-8')
        os.remove(filename)

        return b64_string
