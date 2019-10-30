import urllib.request
import json
import logging
from PIL import Image
from urllib import parse
from flask import current_app as app

from .external_products import register_products
from newsroom.upload import ASSETS_RESOURCE
from newsroom.media_utils import store_image, get_thumbnail, get_watermark

AAP_PHOTOS_TOKEN = 'AAPPHOTOS_TOKEN'
logger = logging.getLogger(__name__)


def set_photo_coverage_href(coverage, planning_item):
    plan_coverage = next(
        (c for c in planning_item.get('coverages') or [] if c.get('coverage_id') == coverage.get('coverage_id')),
        None
    )
    content_type = plan_coverage['planning']['g2_content_type']
    if plan_coverage['workflow_status'] != 'completed' or \
                (content_type in ['picture', 'video', ] and \
            not app.config.get('MULTIMEDIA_WEBSITE_SEARCH_URL')) or \
                (content_type == 'video_explainer' and \
            not app.config.get('EXPLAINERS_WEBSITE_URL')):
        return

    date_range_filter = '"DateRange":[{"Start":"%s"}],"DateCreatedFilter":"false"' % plan_coverage['planning'][
                                                                                        'scheduled'][:10]
    slugline = parse.quote(
        plan_coverage.get('planning', {}).get('slugline', planning_item.get('slugline'))
    )
    keyword_filter = '"SearchKeywords":[{"Keyword":"NZN","Operator":"NOT"}, {"Keyword":"%s","Operator":"AND"}]' % (
        '\\"{}\\"'.format(slugline)
    )

    if content_type == 'video':
        return '{}(credit:"aap video") OR (credit:"pr video")/AAP VIDEO?q={{{}, {}}}'.format(
            app.config.get('MULTIMEDIA_WEBSITE_SEARCH_URL'),
            keyword_filter, date_range_filter)
    elif content_type == 'video_explainer':
        return '{}?q={{{}, {}}}'.format(app.config.get('EXPLAINERS_WEBSITE_URL'), keyword_filter, date_range_filter)
    else:
        return '{}"{}"?q={{"MediaTypes":["image"],{}}}'.format(
            app.config.get('MULTIMEDIA_WEBSITE_SEARCH_URL'),
            slugline, date_range_filter
        )


def _fetch_photos(url):
    headers = {'Authorization': 'Basic {}'.format(app.config.get(AAP_PHOTOS_TOKEN))}
    request = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = response.read()
            json_data = json.loads(data.decode("utf-8"))
            return json_data
    except Exception:
        return {}


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


def generate_preview_details_renditions(picture):
    """Generate preview and details rendition"""
    if not picture or not picture.get('renditions') or not picture.get('renditions').get('16-9'):
        logger.warning('Invalid renditions. picture: {}'.format(picture))
        return

    # add watermark to base/view images
    rendition = picture.get('renditions', {}).get('16-9')
    if rendition:
        binary = app.media.get(rendition['media'], resource=ASSETS_RESOURCE)
        im = Image.open(binary)
        watermark = get_watermark(im)
        custom = store_image(watermark, _id='%s%s' % (rendition['media'], '_newsroom_custom'))
        picture['renditions'].update({
            '_newsroom_custom': custom,
        })


def init_app(app):
    app.set_photo_coverage_href = set_photo_coverage_href
    app.get_media_cards_external = get_media_cards_external
    app.generate_preview_details_renditions = generate_preview_details_renditions
    register_products(app)
