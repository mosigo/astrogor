import configparser
from datetime import datetime, timedelta

import cairo
from flatlib import const
from transliterate import translit

from ext.sf_geocoder import SFGeocoder
from model.sf import SoulFormulaWithBorders, NumericInfo
from model.sf_flatlib import FlatlibBuilder
from utils.sf_csv import read_csv_file
from view.sf_printer import TwoCirclePrinter, OneCirclePrinter


def get_borders(dt: datetime, lat: float, lon: float):
    builder = FlatlibBuilder()
    formula = builder.build_formula(dt, lat=lat, lon=lon)
    formula_id = formula.get_id()
    print(f'ID формулы        => {formula_id}')
    left = dt - timedelta(minutes=1)
    left_formula = builder.build_formula(left, lat=lat, lon=lon)
    while left_formula.get_id() == formula_id:
        left = left - timedelta(minutes=1)
        left_formula = builder.build_formula(left, lat=lat, lon=lon)
    print(f'ID формулы слева  => {left_formula.get_id()}')

    right = dt + timedelta(minutes=1)
    right_formula = builder.build_formula(right, lat=lat, lon=lon)
    while right_formula.get_id() == formula_id:
        right = right + timedelta(minutes=1)
        right_formula = builder.build_formula(right, lat=lat, lon=lon)
    print(f'ID формулы справа => {right_formula.get_id()}')

    return left_formula.dt, right_formula.dt


def print_user_info(name, birthday_time, city, death_time=None):
    name_tr = translit(name, "ru", reversed=True)
    name_tr = name_tr.replace(' ', '_').replace('\'', '').lower()
    name_tr += '.pdf'

    geo_res = geocoder.get_geo_position(city, birthday_time)
    print(f'UTC => {geo_res}')

    builder = FlatlibBuilder()
    # printer = TwoCirclePrinter()
    printer = OneCirclePrinter()

    dt = datetime.strptime(f'{birthday_time} {geo_res.utc_offset}', '%Y-%m-%d %H:%M %z')
    # dt = datetime.strptime(f'{birthday_time} +0400', '%Y-%m-%d %H:%M %z')
    death_dt = None
    if death_time is not None:
        death_dt = datetime.strptime(f'{death_time} {geo_res.utc_offset}', '%Y-%m-%d %H:%M %z')
    formula = builder.build_formula(dt, lat=geo_res.lat, lon=geo_res.lon)
    cosmogram = builder.build_cosmogram(dt, lat=geo_res.lat, lon=geo_res.lon, death_dt=death_dt)
    print(f'Меркурий => {cosmogram.get_planet_info(const.MERCURY).signlon}')
    start_dt, end_dt = get_borders(dt, lat=geo_res.lat, lon=geo_res.lon)

    surface_pdf = cairo.PDFSurface(
        'pic/' + name_tr, printer.width + 2 * printer.border_offset, printer.height + 2 * printer.border_offset)
    printer.print_info(name, geo_res.address,
                       SoulFormulaWithBorders(formula, start_dt, end_dt), cosmogram, NumericInfo(dt), surface_pdf)
    surface_pdf.finish()


if __name__ == '__main__':
    config = configparser.RawConfigParser()
    config.read('sf_config.ini')
    config.read('sf_config_local.ini')

    geocoder = SFGeocoder(config.get('Geocoder', 'token'))

    row = read_csv_file('in_data/user_info.csv')[-1]
    print(row)

    name = row['name']
    birthday = row['birthday']
    city = row['city']
    death_day = row['death_day'] if row['death_day'] else None

    print_user_info(name, birthday, city, death_day)

