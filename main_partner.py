import configparser
import os
from pathlib import Path

import cairo

from datetime import datetime, timedelta

from transliterate import translit

from ext.sf_geocoder import DefaultSFGeocoder
from model.sf import SoulFormulaWithBorders, SoulFormula
from model.sf_flatlib import FlatlibBuilder, get_borders
from utils.sf_csv import read_csv_file
from view.sf_printer import OneCirclePrinter


def find_partner_birthday(name, birthday_time, city, gender:str, cur_city='Москва'):
    geo_res = geocoder.get_geo_position(city, birthday_time)
    print(f'UTC => {geo_res}')

    dt_birthday = datetime.strptime(f'{birthday_time} {geo_res.utc_offset}', '%Y-%m-%d %H:%M %z')
    dt_from = dt_birthday.replace(year=dt_birthday.year - 5)
    dt_to = dt_birthday.replace(year=dt_birthday.year + 5)

    geo_res_now = geocoder.get_geo_position(cur_city, dt_from.strftime('%Y-%m-%d %H:%M'))
    print(f'UTC => {geo_res_now}')

    builder = FlatlibBuilder()
    sf_birthday = builder.build_formula(dt_birthday, lat=geo_res.lat, lon=geo_res.lon)

    partners_orbit = 2 if gender == 'm' else 3
    planets = sf_birthday.orbits.get(partners_orbit, [])

    partner_partners_orbit = 3 if gender == 'm' else 2

    orbit_name = 'Венеры' if partners_orbit == 2 else 'Марса'
    if len(planets) == 0:
        print(f'Нет планет на орбите {orbit_name}, не могу осуществить поиск')
        return
    print(f'На орбите {orbit_name} расположены следующие планеты: {planets}.')

    results = []
    result_ids = set()

    dt = dt_from
    while dt <= dt_to:
        sf = builder.build_formula(dt, lat=geo_res_now.lat, lon=geo_res_now.lon)

        partner_planets_in_partners_orbit = sf.orbits.get(partner_partners_orbit, [])

        partner_is_match = True
        for planet in planets:
            if planet not in sf.center_set:
                partner_is_match = False
                break
            if planet in sf_birthday.retro and planet not in sf.retro:
                partner_is_match = False
                break
            if planet not in sf_birthday.retro and planet in sf.retro:
                partner_is_match = False
                break
            if partner_planets_in_partners_orbit:
                for p in partner_planets_in_partners_orbit:
                    if p not in sf_birthday.center_set:
                        partner_is_match = False
                        break
                    if p in sf.retro and p not in sf_birthday.retro:
                        partner_is_match = False
                        break
                    if p not in sf.retro and p in sf_birthday.retro:
                        partner_is_match = False
                        break

        is_center_similar = len(sf.center_set.intersection(sf_birthday.center_set)) > 0
        sf_id = sf.get_id()
        if partner_is_match and is_center_similar and sf_id not in result_ids:
            result_ids.add(sf_id)
            results.append(sf)

        dt += timedelta(days=1)

    if len(results) > 0:
        name_tr = translit(name, "ru", reversed=True)
        name_tr = name_tr.replace(' ', '_').replace('\'', '').lower()

        dir_name = f'pic/{name_tr}_partners'
        Path(dir_name).mkdir(parents=True, exist_ok=True)

        print_user_info(f'{dir_name}/{name_tr}.pdf', sf_birthday, geo_res, name)

        partner_name = 'Неизвестная' if gender == 'm' else 'Неизвестный'

        num = 1
        for sf in results:
            print('Найдена идеальная пара!')
            print(sf)
            print()

            print_user_info(f'{dir_name}/partner_{num}_{sf.dt.strftime("%Y-%m-%d")}.pdf',
                            sf, geo_res_now, f'{partner_name} {num}')

            num += 1


def print_user_info(file_name: str, sf: SoulFormula, geo_res, name: str):
    dt = sf.dt

    printer = OneCirclePrinter(age_units='years')
    builder = FlatlibBuilder()

    cosmogram = builder.build_cosmogram(dt, lat=geo_res.lat, lon=geo_res.lon)
    start_dt, end_dt = get_borders(dt, lat=geo_res.lat, lon=geo_res.lon)

    surface_pdf = cairo.PDFSurface(
        file_name, printer.width + 2 * printer.border_offset,
                                         printer.height + 2 * printer.border_offset)
    printer.print_info(name, geo_res.address,
                       SoulFormulaWithBorders(sf, start_dt, end_dt), cosmogram,
                       surface_pdf)
    surface_pdf.finish()


if __name__ == '__main__':
    config = configparser.RawConfigParser()
    config.read('sf_config.ini')
    config.read('sf_config_local.ini')

    geocoder = DefaultSFGeocoder(config.get('Geocoder', 'token'))

    row = read_csv_file('in_data/user_info.csv')[-1]

    name = row['name']
    birthday = row['birthday']
    city = row['city']
    gender = row['gender']

    find_partner_birthday(name, birthday, city, gender)

