from ext.sf_geocoder import get_geo_position

if __name__ == '__main__':
    geo_res = get_geo_position('тобольск')

    print(geo_res)

