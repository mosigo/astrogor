from datetime import datetime

import swisseph
from flatlib import const
from flatlib.datetime import Datetime


def dt_to_flatlib_dt(dt: datetime):
    offset = dt.strftime('%z')
    if not offset:
        offset = '+00:00'
    else:
        offset = offset[:3] + ':' + offset[3:5]
    return Datetime(dt.strftime('%Y/%m/%d'), dt.strftime('%H:%M'), offset)


if __name__ == '__main__':
    dt = datetime.strptime(f'1987-01-10 12:00 +0500', '%Y-%m-%d %H:%M %z')
    jd = dt_to_flatlib_dt(dt).jd

    dt1 = datetime.strptime(f'2021-11-27 23:22 +0500', '%Y-%m-%d %H:%M %z')
    jd1 = dt_to_flatlib_dt(dt1).jd
    # print(jd1 - jd)

    swisseph.set_ephe_path('/usr/local/share/ephe')
    sweList, flg = swisseph.calc_ut(jd, 1)

    print(sweList)
    print(flg)

    # print(swisseph.get_planet_name(56))
    # sweList, flg = swisseph.pheno_ut(jd, 56)
    lon = sweList[0]
    res = {
        'id': 'Lilith',
        'lon': lon,
        'lat': sweList[1],
        'lonspeed': sweList[3],
        'latspeed': sweList[4],
        'sign': const.LIST_SIGNS[int(lon / 30)],
        'signlon': lon % 30
    }
    print(res)