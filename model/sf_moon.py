from datetime import datetime

import pytz
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

LUNAR_MONTH_LENGTH = 29.530588853


def _dt_to_flatlib_dt(dt: datetime):
    offset = dt.strftime('%z')
    if not offset:
        offset = '+00:00'
    else:
        offset = offset[:3] + ':' + offset[3:5]
    return Datetime(dt.strftime('%Y/%m/%d'), dt.strftime('%H:%M'), offset)


def get_lunar_day(dt: datetime, lat=55.75322, lon=37.622513) -> float:
    date = _dt_to_flatlib_dt(dt)
    pos = GeoPos(lat, lon)
    res = abs(date.jd - 2451550.1) / LUNAR_MONTH_LENGTH
    return (res - int(res)) * LUNAR_MONTH_LENGTH


if __name__ == '__main__':
    cur_dt = datetime.now(pytz.timezone("Europe/Moscow"))
    print(get_lunar_day(cur_dt))