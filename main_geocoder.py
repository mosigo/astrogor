import configparser

from ext.sf_geocoder import SFGeocoder

if __name__ == '__main__':
    config = configparser.RawConfigParser()
    config.read('sf_config.ini')
    config.read('sf_config_local.ini')

    geocoder = SFGeocoder(config.get('Geocoder', 'token'))
    geo_res = geocoder.get_geo_position('тобольск')

    print(geo_res)

