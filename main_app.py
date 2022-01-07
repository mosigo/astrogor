import base64
import configparser
import os
from urllib.parse import unquote

import pytz

from flask import Flask, request, render_template, send_file, redirect
from datetime import datetime, timedelta

from transliterate import translit

from app.app_sf import generate_full_card, generate_card
from app.app_transit import generate_transit, generate_full_transit
from ext.sf_geocoder import DefaultSFGeocoder

app = Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def index():
    return render_template('old.html')


@app.route('/fd', methods=['GET'])
def fd():
    return redirect('/card')


@app.route('/old', methods=['GET'])
def old():
    return render_template('index.html')


@app.route('/download-card', methods=['GET'])
def download_card():
    fio, birthday, city, age_units = get_card_params()

    birthday_unified = datetime.strptime(birthday, '%d.%m.%Y %H:%M').strftime('%Y-%m-%d %H:%M')
    filename = generate_full_card(geocoder, fio, f'{birthday_unified}', city, age_units)
    return send_file(filename)


def get_card_params():
    cur_dt = datetime.now(pytz.timezone("Europe/Moscow"))

    fio = request.args.get('fio', 'Сегодня')
    birthday = request.args.get('birthday', cur_dt.strftime('%d.%m.%Y %H:%M'))
    city = request.args.get('city', 'Москва')
    age_units = 'years' if request.args.get('age-in-years', False) else 'days'

    return fio, birthday, city, age_units


@app.route('/card', methods=['GET'])
def create_card():
    fio, birthday, city, age_units = get_card_params()

    birthday_unified = datetime.strptime(birthday, '%d.%m.%Y %H:%M').strftime('%Y-%m-%d %H:%M')
    filename = generate_card(geocoder, fio, f'{birthday_unified}', city, age_units)

    name_tr = translit(fio, "ru", reversed=True)
    name_tr = name_tr.replace(' ', '_').replace('\'', '').lower()
    out_file = f'{name_tr}_{birthday_unified[:10]}.pdf'

    age_in_years = '&age-in-years=on' if age_units == 'years' else ''
    link = '/download-card?fio=' + unquote(fio) + '&birthday=' + unquote(birthday) + '&city=' + unquote(city) + \
           age_in_years

    with open(filename, "rb") as img_file:
        b64_string = base64.b64encode(img_file.read()).decode('utf-8')
        os.remove(filename)
        return render_template('card.html', img_as_base64=b64_string,
                               fio=fio, birthday=birthday, city=city,
                               out_file_name=out_file, download_link=link, age_in_years=age_units == 'years')


def get_transit_params():
    cur_dt = datetime.now(pytz.timezone("Europe/Moscow"))

    fio = request.args.get('fio', 'Сегодня')
    birthday = request.args.get('birthday', cur_dt.strftime('%d.%m.%Y %H:%M'))
    transit_day = request.args.get('transit-day', cur_dt.strftime('%d.%m.%Y %H:%M'))
    city = request.args.get('city', 'Москва')
    cur_city = request.args.get('current-city', 'Москва')

    return fio, birthday, city, transit_day, cur_city


@app.route('/transit', methods=['GET'])
def create_transit():
    fio, birthday, city, transit_day, cur_city = get_transit_params()

    birthday_dt = datetime.strptime(birthday, '%d.%m.%Y %H:%M')
    transit_dt = datetime.strptime(transit_day, '%d.%m.%Y %H:%M')

    filename = generate_transit(geocoder, birthday_dt, city, transit_dt, cur_city)

    name_tr = translit(fio, "ru", reversed=True)
    name_tr = name_tr.replace(' ', '_').replace('\'', '').lower()
    birthday_unified = birthday_dt.strftime('%Y-%m-%d %H:%M')
    transit_day_unified = transit_dt.strftime('%Y-%m-%d %H:%M')
    out_file = f'{name_tr}_tr{birthday_unified[:10]}_to{transit_day_unified[:10]}.pdf'

    params = 'fio=' + unquote(fio) + '&birthday=' + unquote(birthday) + '&city=' + unquote(city) + \
           '&current-city=' + unquote(cur_city)

    next_transit_day = (transit_dt + timedelta(days=1)).strftime('%d.%m.%Y %H:%M')
    prev_transit_day = (transit_dt - timedelta(days=1)).strftime('%d.%m.%Y %H:%M')

    next_link = '/transit?' + params + '&transit-day=' + unquote(next_transit_day)
    prev_link = '/transit?' + params + '&transit-day=' + unquote(prev_transit_day)
    link = '/download-transit?' + params + '&transit-day=' + unquote(transit_day)

    with open(filename, "rb") as img_file:
        b64_string = base64.b64encode(img_file.read()).decode('utf-8')
        os.remove(filename)
        return render_template('transit.html', img_as_base64=b64_string,
                               fio=fio, birthday=birthday, city=city, transit_day=transit_day, current_city=cur_city,
                               out_file_name=out_file, download_link=link, prev_link=prev_link, next_link=next_link)


@app.route('/download-transit', methods=['GET'])
def download_transit():
    fio, birthday, city, transit_day, cur_city = get_transit_params()

    birthday_dt = datetime.strptime(birthday, '%d.%m.%Y %H:%M')
    transit_dt = datetime.strptime(transit_day, '%d.%m.%Y %H:%M')
    filename = generate_full_transit(geocoder, birthday_dt, city, transit_dt, cur_city)
    return send_file(filename)


if __name__ == '__main__':
    config = configparser.RawConfigParser()
    config.read('sf_config.ini')
    config.read('sf_config_local.ini')

    geocoder = DefaultSFGeocoder(config.get('Geocoder', 'token'))

    app.run(debug=True, port=8080)
