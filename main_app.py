import base64
import configparser
import os
from urllib.parse import unquote

import pytz

from flask import Flask, request, render_template, send_file, redirect, send_from_directory
from datetime import datetime, timedelta

from transliterate import translit

from logging.config import dictConfig

from app.app_sf import generate_full_card, generate_card
from app.app_transit import generate_transit, generate_full_transit, get_nearest_transit_connections
from ext.sf_geocoder import DefaultSFGeocoder

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__)


def print_real_ip(method_name: str) -> str:
    ip = request.headers.get('X-Real-IP', '')
    app.logger.info(f'Метод {method_name} вызван с IP = {ip}.')
    return ip


def get_date_param_value(param_name: str, param_default_value: datetime) -> datetime:
    val = request.args.get(param_name)
    if val:
        try:
            return datetime.strptime(val, '%d.%m.%Y %H:%M')
        except:
            pass
    return param_default_value


def get_str_param_value(param_name: str, param_default_value: str) -> str:
    val = request.args.get(param_name)
    if val and val.strip():
        return val
    return param_default_value


def get_bool_param_value(param_name: str, param_default_value: bool) -> bool:
    val = request.args.get(param_name)
    if val and val == 'on':
        return True
    return param_default_value


@app.route('/fd', methods=['GET'])
def fd():
    print_real_ip('fd')
    return redirect('/card')


@app.route('/', methods=['GET'])
def index():
    print_real_ip('/')
    return render_template('index.html')


@app.route('/edu', methods=['GET'])
def edu():
    print_real_ip('edu')
    return render_template('edu.html')


@app.route('/contacts', methods=['GET'])
def contacts():
    print_real_ip('contacts')
    return render_template('contacts.html')


@app.route('/books', methods=['GET'])
def books():
    print_real_ip('books')
    return render_template('books.html')


@app.route('/videos', methods=['GET'])
def videos():
    print_real_ip('videos')
    return render_template('videos.html')


@app.route('/astro', methods=['GET'])
def astro():
    print_real_ip('astro')
    return render_template('astro.html')


@app.route('/others', methods=['GET'])
def others():
    print_real_ip('others')
    return render_template('others.html')


@app.route('/consultations', methods=['GET'])
def consultations():
    print_real_ip('consultations')
    return render_template('consultations.html')


@app.route('/news', methods=['GET'])
def news():
    print_real_ip('news')
    return render_template('news.html')


@app.route('/courses/fd', methods=['GET'])
def course_fd():
    print_real_ip('courses/fd')
    return render_template('courses/fd.html')


@app.route('/courses/astro', methods=['GET'])
def course_astro():
    print_real_ip('courses/astro')
    return render_template('courses/astro.html')


@app.route('/courses/karma', methods=['GET'])
def course_karma():
    print_real_ip('courses/karma')
    return render_template('courses/karma.html')


@app.route('/courses/palmistry', methods=['GET'])
def course_palmistry():
    print_real_ip('courses/palmistry')
    return render_template('courses/palmistry.html')


@app.route('/robots.txt', methods=['GET'])
def robots_txt():
    print_real_ip('robots.txt')
    return send_from_directory('templates', 'robots.txt')


@app.route('/download-card', methods=['GET'])
def download_card():
    print_real_ip('download-card')
    fio, birthday, city, age_units = get_card_params()

    birthday_unified = birthday.strftime('%Y-%m-%d %H:%M')
    filename = generate_full_card(geocoder, fio, f'{birthday_unified}', city, age_units)
    return send_file(filename)


def get_card_params():
    cur_dt = datetime.now(pytz.timezone("Europe/Moscow"))

    fio = get_str_param_value('fio', 'Сегодня')
    birthday = get_date_param_value('birthday', cur_dt)
    city = get_str_param_value('city', 'Москва')
    age_units = 'years' if request.args.get('age-in-years', False) else 'days'

    return fio, birthday, city, age_units


@app.route('/card', methods=['GET'])
def create_card():
    print_real_ip('card')
    fio, birthday, city, age_units = get_card_params()

    birthday_as_str = birthday.strftime('%d.%m.%Y %H:%M')

    birthday_unified = birthday.strftime('%Y-%m-%d %H:%M')
    filename = generate_card(geocoder, fio, f'{birthday_unified}', city, age_units)

    name_tr = translit(fio, "ru", reversed=True)
    name_tr = name_tr.replace(' ', '_').replace('\'', '').lower()
    out_file = f'{name_tr}_{birthday_unified[:10]}.pdf'

    age_in_years = '&age-in-years=on' if age_units == 'years' else ''
    link = '/download-card?fio=' + unquote(fio) + '&birthday=' + unquote(birthday_as_str) \
           + '&city=' + unquote(city) + age_in_years

    transit_link = '/transit?' + unquote_str_param('fio', fio) + \
                   unquote_str_param('birthday', birthday_as_str) + unquote_str_param('city', city)

    with open(filename, "rb") as img_file:
        b64_string = base64.b64encode(img_file.read()).decode('utf-8')
        os.remove(filename)
        return render_template('card.html', img_as_base64=b64_string,
                               fio=fio, birthday=birthday_as_str, city=city,
                               out_file_name=out_file, download_link=link, age_in_years=age_units == 'years',
                               transit_link=transit_link)


def get_transit_params():
    cur_dt = datetime.now(pytz.timezone("Europe/Moscow"))

    fio = get_str_param_value('fio', 'Сегодня')
    birthday = get_date_param_value('birthday', cur_dt)
    transit_day = get_date_param_value('transit-day', cur_dt)
    city = get_str_param_value('city', 'Москва')
    cur_city = get_str_param_value('current-city', 'Москва')

    show_source = get_bool_param_value('show-source', False)
    show_source_to_transit = get_bool_param_value('show-source-to-transit', False)
    show_transit = get_bool_param_value('show-transit', False)

    return fio, birthday, city, transit_day, cur_city, show_source, show_source_to_transit, show_transit


def unquote_str_param(param_name: str, param_value: str) -> str:
    return f'&{param_name}={unquote(param_value)}'


def unquote_bool_param(param_name: str, param_value: bool) -> str:
    if param_value:
        return f'&{param_name}=on'
    return ''


@app.route('/transit', methods=['GET'])
def create_transit():
    ip = print_real_ip('transit')
    # пытаемся отдать роботу Яндекса 404 — временная мера
    if request.args.get('birthday') and ip in ['141.8.142.67', '141.8.142.78', '141.8.142.94', '213.180.203.12',
                                               '213.180.203.175', '213.180.203.183', '213.180.203.20',
                                               '213.180.203.249', '213.180.203.252', '213.180.203.5', '213.180.203.66',
                                               '213.180.203.67', '213.180.203.85', '213.180.203.89', '213.180.203.91',
                                               '213.180.203.96', '5.255.253.113', '5.255.253.130', '5.255.253.148',
                                               '5.255.253.164', '5.255.253.165', '5.255.253.177', '5.45.207.112',
                                               '5.45.207.115', '5.45.207.126', '5.45.207.133', '5.45.207.142',
                                               '5.45.207.65', '5.45.207.71', '5.45.207.72', '87.250.224.101',
                                               '87.250.224.103', '87.250.224.138', '87.250.224.139', '87.250.224.146',
                                               '87.250.224.16', '87.250.224.181', '87.250.224.189', '87.250.224.190',
                                               '87.250.224.193', '87.250.224.198', '87.250.224.21', '87.250.224.27',
                                               '87.250.224.40', '87.250.224.48', '87.250.224.52', '87.250.224.60',
                                               '87.250.224.70', '87.250.224.74', '87.250.224.76', '95.108.213.10',
                                               '95.108.213.15', '95.108.213.24', '95.108.213.26', '95.108.213.27',
                                               '95.108.213.4', '95.108.213.41', '95.108.213.69', '95.108.213.71']:
        return page_not_found(None)

    fio, birthday_dt, city, transit_dt, cur_city, show_source, show_source_to_transit, show_transit = \
        get_transit_params()

    birthday = birthday_dt.strftime('%d.%m.%Y %H:%M')
    transit_day = transit_dt.strftime('%d.%m.%Y %H:%M')

    filename = generate_transit(geocoder, birthday_dt, city, transit_dt, cur_city,
                                show_source, show_source_to_transit, show_transit)

    name_tr = translit(fio, "ru", reversed=True)
    name_tr = name_tr.replace(' ', '_').replace('\'', '').lower()
    birthday_unified = birthday_dt.strftime('%Y-%m-%d %H:%M')
    transit_day_unified = transit_dt.strftime('%Y-%m-%d %H:%M')
    out_file = f'{name_tr}_tr{birthday_unified[:10]}_to{transit_day_unified[:10]}.pdf'

    params = unquote_str_param('fio', fio) + unquote_str_param('birthday', birthday) + \
             unquote_str_param('city', city) + unquote_str_param('current-city', cur_city) + \
             unquote_bool_param('show-source', show_source) + \
             unquote_bool_param('show-source-to-transit', show_source_to_transit) + \
             unquote_bool_param('show-transit', show_transit)

    next_transit_day = (transit_dt + timedelta(days=1)).strftime('%d.%m.%Y %H:%M')
    prev_transit_day = (transit_dt - timedelta(days=1)).strftime('%d.%m.%Y %H:%M')

    next_link = '/transit?' + params + '&transit-day=' + unquote(next_transit_day)
    prev_link = '/transit?' + params + '&transit-day=' + unquote(prev_transit_day)

    next_transit_hour = (transit_dt + timedelta(hours=1)).strftime('%d.%m.%Y %H:%M')
    prev_transit_hour = (transit_dt - timedelta(hours=1)).strftime('%d.%m.%Y %H:%M')

    next_link_hour = '/transit?' + params + '&transit-day=' + unquote(next_transit_hour)
    prev_link_hour = '/transit?' + params + '&transit-day=' + unquote(prev_transit_hour)

    link = '/download-tr?' + params + '&transit-day=' + unquote(transit_day)

    fd_link = '/card?' + \
              unquote_str_param('fio', fio) + unquote_str_param('birthday', birthday) + unquote_str_param('city', city)

    planet_to_connection, planet_to_view = get_nearest_transit_connections(geocoder, birthday_dt, city, transit_dt,
                                                                           cur_city)
    planet_to_connection_res = []
    for planet, (planet_to, dt, _) in planet_to_connection.items():
        dt_as_str = dt.strftime('%d.%m.%Y %H:%M')
        tr_link = '/transit?' + params + '&transit-day=' + unquote(dt_as_str)
        planet_to_connection_res.append((planet, planet_to, dt.strftime('%d.%m.%Y'), tr_link, dt))
    planet_to_connection_res.sort(key=lambda a: a[4])

    with open(filename, "rb") as img_file:
        b64_string = base64.b64encode(img_file.read()).decode('utf-8')
        os.remove(filename)
        return render_template('transit.html', img_as_base64=b64_string,
                               fio=fio, birthday=birthday, city=city, transit_day=transit_day, current_city=cur_city,
                               out_file_name=out_file, download_link=link, prev_link=prev_link, next_link=next_link,
                               prev_link_hour=prev_link_hour, next_link_hour=next_link_hour,
                               show_source=show_source, show_source_to_transit=show_source_to_transit,
                               show_transit=show_transit, fd_link=fd_link,
                               planet_to_connection=planet_to_connection_res, planet_to_connection_view=planet_to_view)


@app.route('/download-tr', methods=['GET'])
def download_transit():
    print_real_ip('download-tr')
    fio, birthday_dt, city, transit_dt, cur_city, show_source, show_source_to_transit, show_transit = \
        get_transit_params()

    filename = generate_full_transit(geocoder, fio, birthday_dt, city, transit_dt, cur_city,
                                     show_source, show_source_to_transit, show_transit)
    return send_file(filename)


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500


@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


if __name__ == '__main__':
    config = configparser.RawConfigParser()
    config.read('sf_config.ini')
    config.read('sf_config_local.ini')

    geocoder = DefaultSFGeocoder(config.get('Geocoder', 'token'))

    debug = False
    if config.has_section('App'):
        debug = config.get('App', 'debug')

    app.run(debug=debug, port=8080)
