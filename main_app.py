import base64
import configparser
import os
import tempfile
import cairo
import pytz

from flask import Flask, request, render_template
from datetime import datetime

from model.sf import SoulFormulaWithBorders, NumericInfo
from model.sf_flatlib import FlatlibBuilder
from ext.sf_geocoder import SFGeocoder
from view.sf_printer import OneCirclePrinter

app = Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def index():
    return render_template('index.html')


@app.route('/fd', methods=['GET'])
def fd():
    return render_template('fd.html')


@app.route('/old', methods=['GET'])
def old():
    return render_template('old.html')


@app.route('/card', methods=['GET'])
def create_card():
    cur_dt = datetime.now(pytz.timezone("Europe/Moscow"))

    fio = request.args.get('fio', 'Сегодняшний день')
    birthday = request.args.get('birthday', cur_dt.strftime('%d.%m.%Y'))
    birth_time = request.args.get('birth_time', cur_dt.strftime('%H:%M'))
    city = request.args.get('city', 'Москва')

    birthday_unified = datetime.strptime(birthday, '%d.%m.%Y').strftime('%Y-%m-%d')
    filename = generate_card(fio, f'{birthday_unified} {birth_time}', city)

    # cur_dt_str = cur_dt.strftime('%d.%m.%Y %H:%M мск')
    # builder = FlatlibBuilder()
    # cosmo = builder.build_cosmogram(
    #     cur_dt
    # )

    # drawer = DefaultCosmogramDrawer(life_years=29.436 * 360 / (360 + 23.82), first_life_year=1, first_life_year_lon=252)
    # drawer = DefaultCosmogramDrawer(aspects=[60], planet_ruler_place='in_sign')
    # surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 2000, 2000)
    # cr = cairo.Context(surface)
    # cr.scale(2000, 2000)
    # drawer.draw_cosmogram(cosmo, cr)
    #
    # new_file, filename = tempfile.mkstemp(suffix='.png', prefix='cosmo_')
    # print(f'Создан временный файл для вывода космограммы: {filename}')
    # surface.write_to_png(filename)
    # os.close(new_file)

    with open(filename, "rb") as img_file:
        b64_string = base64.b64encode(img_file.read()).decode('utf-8')
        os.remove(filename)
        return render_template('card.html', img_as_base64=b64_string)


def generate_card(name, birthday_time, city, death_time=None):

    geo_res = geocoder.get_geo_position(city, birthday_time)
    print(f'UTC => {geo_res}')

    w, h = 210 * 10, 297 * 10

    builder = FlatlibBuilder()
    printer = OneCirclePrinter(width=w, height=h, border_offset=50, title_height=80, subtitle_height=40,
                               text_offset=20, add_info_radius=180, add_info_overlap=25, qr_width=250)

    dt = datetime.strptime(f'{birthday_time} {geo_res.utc_offset}', '%Y-%m-%d %H:%M %z')
    death_dt = None
    if death_time is not None:
        death_dt = datetime.strptime(f'{death_time} {geo_res.utc_offset}', '%Y-%m-%d %H:%M %z')
    formula = builder.build_formula(dt, lat=geo_res.lat, lon=geo_res.lon)
    cosmogram = builder.build_cosmogram(dt, lat=geo_res.lat, lon=geo_res.lon, death_dt=death_dt)
    # start_dt, end_dt = get_borders(dt, lat=geo_res.lat, lon=geo_res.lon)
    start_dt, end_dt = dt, dt

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cr = cairo.Context(surface)
    cr.scale(w, w)
    printer.print_info(name, geo_res.address,
                       SoulFormulaWithBorders(formula, start_dt, end_dt), cosmogram, NumericInfo(dt), surface)

    new_file, filename = tempfile.mkstemp(suffix='.png', prefix='cosmo_')
    print(f'Создан временный файл для вывода космограммы: {filename}')
    surface.write_to_png(filename)
    os.close(new_file)

    surface.finish()
    return filename


if __name__ == '__main__':
    config = configparser.RawConfigParser()
    config.read('sf_config.ini')
    config.read('sf_config_local.ini')

    geocoder = SFGeocoder(config.get('Geocoder', 'token'))

    app.run(debug=True, port=8080)
