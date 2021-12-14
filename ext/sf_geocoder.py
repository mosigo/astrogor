import requests
import pytz

from timezonefinder import TimezoneFinder
from datetime import datetime, timedelta


class GeocoderResult:

    def __init__(self, address: str, lat: float, lon: float, utc_offset: str) -> None:
        self.utc_offset = utc_offset
        self.lon = lon
        self.lat = lat
        self.address = address

    def __str__(self) -> str:
        s = self.address + '\n'
        s += f'lon={self.lon}, lat={self.lat}\n'
        s += self.utc_offset
        return s

    def __repr__(self) -> str:
        return self.__str__()


def get_geo_position(address: str, dt_str: str) -> GeocoderResult:
    r = requests.get(
        'https://geocode-maps.yandex.ru/1.x',
        params={
            'geocode': address,
            'apikey': '',
            'format': 'json',
            'lang': 'ru_RU'
        }
    )
    if r.status_code == 200:
        rj = r.json()
        addresses = rj['response']['GeoObjectCollection']['featureMember']
        if len(addresses) > 0:
            address = addresses[0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['Address']['formatted']
            point = addresses[0]['GeoObject']['Point']['pos']

            lon, lat = point.split(' ')
            lon, lat = float(lon), float(lat)
            tz_finder = TimezoneFinder()
            tz_name = tz_finder.timezone_at(lng=lon, lat=lat)
            tz = pytz.timezone(tz_name)
            dt = tz.localize(datetime.strptime(dt_str, '%Y-%m-%d %H:%M'))
            offset = dt.strftime('%z')
            return GeocoderResult(address, lat, lon, offset)
    else:
        print(r.text)
    return None
