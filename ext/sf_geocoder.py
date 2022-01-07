from abc import abstractmethod
from typing import Dict, Any

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


class YaGeocoder:

    def __init__(self, token) -> None:
        self.token = token

    def geocode(self, address: str) -> (str, (float, float)):
        r = requests.get(
            'https://geocode-maps.yandex.ru/1.x',
            params={
                'geocode': address,
                'apikey': self.token,
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

                return address, (lat, lon)
        else:
            print(r.text)
        return None


class CachedYaGeocoder:
    cache: {str, (str, (float, float))}

    def __init__(self, token) -> None:
        self.base_geocoder = YaGeocoder(token)
        self.cache = {}

    @staticmethod
    def unify_query(query: str) -> str:
        return query.lower().strip()

    def geocode(self, src_address: str) -> (str, (float, float)):
        address = self.unify_query(src_address)
        res = self.cache.get(address)
        if res:
            print(f'Возвращён закешированный результат геокодера на запрос «{address}»')
            return res
        res = self.base_geocoder.geocode(address)
        print(f'Возвращён новый результат геокодера на запрос «{address}»')
        if res:
            self.cache[address] = res
        return res


class SFGeocoder:

    @abstractmethod
    def get_geo_position(self, address: str, dt_str: str) -> GeocoderResult:
        pass


class DefaultSFGeocoder(SFGeocoder):

    def __init__(self, token) -> None:
        self.ya_geocoder = CachedYaGeocoder(token)

    def get_geo_position(self, src_address: str, dt_str: str) -> GeocoderResult:

        ya_geocoder_result = self.ya_geocoder.geocode(src_address)
        if ya_geocoder_result:
            address, (lat, lon) = ya_geocoder_result
            tz_finder = TimezoneFinder()
            tz_name = tz_finder.timezone_at(lng=lon, lat=lat)
            tz = pytz.timezone(tz_name)
            dt = tz.localize(datetime.strptime(dt_str, '%Y-%m-%d %H:%M'))
            offset = dt.strftime('%z')
            return GeocoderResult(address, lat, lon, offset)
        return None

