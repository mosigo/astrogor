import os
import tempfile

import cairo

from datetime import datetime

from model.sf import SoulFormulaWithBorders
from model.sf_flatlib import FlatlibBuilder, get_borders
from view.sf_printer import OneCirclePrinter


def generate_full_card(geocoder, name, birthday_time, city, age_units):
    geo_res = geocoder.get_geo_position(city, birthday_time)

    builder = FlatlibBuilder()
    printer = OneCirclePrinter(age_units=age_units)

    dt = datetime.strptime(f'{birthday_time} {geo_res.utc_offset}', '%Y-%m-%d %H:%M %z')
    formula = builder.build_formula(dt, lat=geo_res.lat, lon=geo_res.lon)
    cosmogram = builder.build_cosmogram(dt, lat=geo_res.lat, lon=geo_res.lon)
    start_dt, end_dt = get_borders(dt, lat=geo_res.lat, lon=geo_res.lon)

    new_file, filename = tempfile.mkstemp(suffix='.pdf', prefix='cosmofd_')

    surface_pdf = cairo.PDFSurface(
        filename, printer.width + 2 * printer.border_offset, printer.height + 2 * printer.border_offset)
    printer.print_info(name, geo_res.address,
                       SoulFormulaWithBorders(formula, start_dt, end_dt), cosmogram, surface_pdf)
    surface_pdf.finish()
    os.close(new_file)

    return filename


def generate_card(geocoder, name, birthday_time, city, age_units):

    geo_res = geocoder.get_geo_position(city, birthday_time)

    w, h = 210 * 10, 275 * 10

    builder = FlatlibBuilder()
    printer = OneCirclePrinter(width=w, height=h, border_offset=0, title_height=0, subtitle_height=0,
                               text_offset=0, add_info_radius=180, add_info_overlap=25, qr_width=0,
                               age_units=age_units, with_titles=False)

    dt = datetime.strptime(f'{birthday_time} {geo_res.utc_offset}', '%Y-%m-%d %H:%M %z')
    formula = builder.build_formula(dt, lat=geo_res.lat, lon=geo_res.lon)
    cosmogram = builder.build_cosmogram(dt, lat=geo_res.lat, lon=geo_res.lon)
    start_dt, end_dt = get_borders(dt, lat=geo_res.lat, lon=geo_res.lon)

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cr = cairo.Context(surface)
    cr.scale(w, w)
    printer.print_info(name, geo_res.address,
                       SoulFormulaWithBorders(formula, start_dt, end_dt), cosmogram, surface)

    new_file, filename = tempfile.mkstemp(suffix='.png', prefix='cosmo_')
    print(f'Создан временный файл для вывода космограммы: {filename}')
    surface.write_to_png(filename)
    os.close(new_file)

    surface.finish()
    return filename