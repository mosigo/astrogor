# pip install sparqlwrapper
# https://rdflib.github.io/sparqlwrapper/

import sys
import requests
import time
from SPARQLWrapper import SPARQLWrapper, JSON
from datetime import datetime, timedelta


def get_results(endpoint_url, query):
    user_agent = "User-Agent: MosigoBot/0.0"
    # TODO adjust user agent; see https://w.wiki/CX6
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


def get_description_by_wiki_id(wiki_id):
    r = requests.get(
        f'https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&ids={wiki_id}&sitefilter=ruwiki')
    if r.status_code == 200:
        res = r.json()['entities'][wiki_id]
        page_id = res['pageid']
        descriptions = res['descriptions']
        description = descriptions.get('ru')
        if description:
            return page_id, description['value']
        description = descriptions.get('en')
        if description:
            return page_id, description['value']
        return page_id, ''
    return 0, ''


def get_by_date(date_as_str):
    endpoint_url = "https://query.wikidata.org/sparql"

    query = """SELECT ?item ?itemLabel 
    WHERE
    {
      ?item  p:P569/ps:P569 "%sT00:00:00Z"^^xsd:dateTime
      SERVICE wikibase:label { bd:serviceParam wikibase:language "ru". }
    }""" % date_as_str

    res = []
    results = get_results(endpoint_url, query)
    for result in results["results"]["bindings"]:
        if result['itemLabel'].get('xml:lang') == 'ru':
            name = result['itemLabel']['value']
            link_with_id = result['item']['value']
            wiki_id = link_with_id.replace('http://www.wikidata.org/entity/', '')
            wiki_link = 'https://ru.wikipedia.org/wiki/' + name.replace(' ', '_')
            res.append(
                (name, wiki_id, wiki_link)
            )
    return res


if __name__ == '__main__':

    f = open(
        '/Users/mosigo/Yandex.Disk.localized/Documents/PycharmProjects/Astrogor/data/wiki_people.csv',
        'w', encoding='utf8')
    f.write(f'дата;wiki id;page id;имя;профессия;ссылка\n')

    dt_start = datetime.strptime('1983-12-09', '%Y-%m-%d')
    dt_end = datetime.strptime('2021-11-04', '%Y-%m-%d')
    # dt_end = datetime.strptime('1900-01-03', '%Y-%m-%d')
    while dt_start <= dt_end:
        print(dt_start)
        date_as_str = dt_start.strftime('%Y-%m-%d')
        i = 0
        while i < 3:
            try:
                for name, wiki_id, wiki_link in get_by_date(date_as_str):
                    page_id, description = get_description_by_wiki_id(wiki_id)
                    print(name, wiki_id, wiki_link, description, page_id)
                    f.write(f'{date_as_str};{wiki_id};{page_id};{name};{description};{wiki_link}\n')
                    f.flush()
                dt_start += timedelta(days=1)
                time.sleep(1)
                break
            except Exception as e:
                print(e)
                time.sleep(60)
                i += 1
    f.close()
