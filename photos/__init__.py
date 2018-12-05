import urllib.request
import json
import logging
from datetime import datetime
from urllib import parse
from flask import current_app as app
from superdesk.utc import utc_to_local

AAP_PHOTOS_TOKEN = 'AAPPHOTOS_TOKEN'
logger = logging.getLogger(__name__)


def set_photo_coverage_href(coverage, planning_item):
    if app.config.get('MULTIMEDIA_WEBSITE_SEARCH_URL') and \
            coverage['planning']['g2_content_type'] == 'picture' and \
            coverage['workflow_status'] == 'completed':
        slugline = coverage.get('planning', {}).get('slugline', planning_item.get('slugline'))
        # converting the coverage schedule date to local time
        local_date = datetime.strftime(
            utc_to_local(
                app.config.get('DEFAULT_TIMEZONE'),
                datetime.strptime(coverage['planning']['scheduled'], '%Y-%m-%dT%H:%M:%S%z')
            ),
            '%Y-%m-%dT%H:%M:%S%z'
        )
        q = '{"DateRange":[{"Start":"%s"}],"DateCreatedFilter":"true"}' % local_date[:10]
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
    assets = set()
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
            asset_count = 0
            for asset in data.get('Assets'):
                asset_id = asset.get('AssetId')
                if asset_count >= count:
                    break
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

                if asset_count < count and asset_id not in assets:
                    cards.append({
                        'media_url': asset.get('Layout', {}).get('Href'),
                        'description': asset.get('Title'),
                        'href': href
                    })
                    assets.add(asset_id)
                    asset_count += 1

    app.cache.set(cache_key, cards, timeout=300)
    return cards


def init_app(app):
    app.set_photo_coverage_href = set_photo_coverage_href
    app.get_media_cards_external = get_media_cards_external
