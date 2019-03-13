
import os
from newsroom.default_settings import BLUEPRINTS as blueprints, CORE_APPS, CLIENT_CONFIG

if os.environ.get('PUSH'):
    BLUEPRINTS = blueprints
else:
    BLUEPRINTS = [blueprint for blueprint in blueprints if 'push' not in blueprint]

BLUEPRINTS.append('newsroom.am_news')
BLUEPRINTS.append('newsroom.market_place')
BLUEPRINTS.append('aap_public')


INSTALLED_APPS = [
    'instrumentation',
    'photos',
    'newsroom.am_news',
    'newsroom.market_place',
    'newsroom-defaults',
]

CLIENT_TIME_FORMAT = 'HH:mm'
CLIENT_DATE_FORMAT = 'DD/MM/YYYY'
SITE_NAME = 'AAP Newsroom'
COPYRIGHT_HOLDER = 'AAP'
COPYRIGHT_NOTICE = ''
USAGE_TERMS = ''
LANGUAGES = ['en']
DEFAULT_LANGUAGE = 'en'
MULTIMEDIA_WEBSITE_URL = os.environ.get('MULTIMEDIA_WEBSITE_URL', 'https://photos.aap.com.au')
MULTIMEDIA_WEBSITE_SEARCH_URL = '{}/{}/'.format(MULTIMEDIA_WEBSITE_URL,
                                                os.environ.get('MULTIMEDIA_WEBSITE_SEARCH_PATH', 'search'))
VIDEOS_WEBSITE_URL = os.environ.get('VIDEOS_WEBSITE_URL', 'https://photos.aap.com.au/galleries/Newsroom/Video')
EXPLAINERS_WEBSITE_URL = os.environ.get('EXPLAINERS_WEBSITE_URL',
                                        'https://photos.aap.com.au/search/(supplementalcategory'
                                        ':VIDEXP)/Visual%20Explainers')
FACTCHECK_WEBSITE_URL = os.environ.get('FACTCHECK_WEBSITE_URL', 'https://factcheck.aap.com.au/')
CLIENT_CONFIG['list_animations'] = False
