import urllib.request
import json
import logging

from urllib import parse
from flask import current_app as app

AAP_PHOTOS_TOKEN = 'AAPPHOTOS_TOKEN'
logger = logging.getLogger(__name__)


def set_photo_coverage_href(coverage, planning_item):
    if app.config.get('MULTIMEDIA_WEBSITE_SEARCH_URL') and \
            coverage['planning']['g2_content_type'] == 'picture' and \
            coverage['workflow_status'] == 'completed':
        slugline = coverage.get('planning', {}).get('slugline', planning_item.get('slugline'))
        q = '{"DateRange":[{"Start":"%s"}],"DateCreatedFilter":"true"}' % coverage['planning']['scheduled'][:10]
        return '{}"{}"?q={}'.format(app.config.get('MULTIMEDIA_WEBSITE_SEARCH_URL'), slugline, q)


def _fetch_photos(url):
    headers = {'Authorization': 'Basic {}'.format(app.config.get(AAP_PHOTOS_TOKEN))}
    request = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = response.read()
            json_data = json.loads(data.decode("utf-8"))
            return json_data
    except Exception:
        return []


def get_media_cards_external(card):
    if not app.config.get('AAPPHOTOS_TOKEN') or not card.get('config') or not card.get('config').get('sources'):
        return []

    cache_key = 'home_photos_{}'.format(card.get('_id'))
    if app.cache.get(cache_key):
        return app.cache.get(cache_key)

    cards = []
    for item in card.get('config').get('sources'):
        if not item.get('url'):
            continue
        data = _fetch_photos(item.get('url'))
        count = int(item.get('count') or 1)
        if data.get('GalleryContainers'):
            containers = data.get('GalleryContainers')[:count]
            for container in containers:
                cards.append({
                    'media_url': container.get('SlotPictureLink'),
                    'description': container.get('Heading'),
                    'href': '{}/{}'.format(
                        app.config.get('MULTIMEDIA_WEBSITE_URL'),
                        container.get('Link')
                    )
                })
        elif data.get('Assets'):
            for asset in data.get('Assets')[:count]:
                parsed_url = parse.parse_qsl(item.get('url'))
                search = None
                query_string = []
                for url_item in parsed_url:
                    key, value = url_item
                    if 'query' in key.lower():
                        search = parse.quote(value)
                    else:
                        query_string.append(url_item)

                href = app.config.get('MULTIMEDIA_WEBSITE_URL')
                if search:
                    href = '{}{}?{}'.format(
                        app.config.get('MULTIMEDIA_WEBSITE_SEARCH_URL'),
                        search,
                        parse.urlencode(query_string)
                    )

                cards.append({
                    'media_url': asset.get('Layout', {}).get('Href'),
                    'description': asset.get('Title'),
                    'href': href
                })

    app.cache.set(cache_key, cards, timeout=300)
    return cards


def init_app(app):
    app.set_photo_coverage_href = set_photo_coverage_href
    app.get_media_cards_external = get_media_cards_external
