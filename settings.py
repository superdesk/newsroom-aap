
import os
from newsroom.default_settings import BLUEPRINTS as blueprints, CORE_APPS

if os.environ.get('PUSH'):
    BLUEPRINTS = blueprints
else:
    BLUEPRINTS = [blueprint for blueprint in blueprints if 'push' not in blueprint]

BLUEPRINTS.append('newsroom.am_news')
BLUEPRINTS.append('newsroom.market_place')

INSTALLED_APPS = [
    'instrumentation',
    'photos',
    'newsroom.am_news',
    'newsroom.market_place',
]

CLIENT_TIME_FORMAT = 'HH:mm'
CLIENT_DATE_FORMAT = 'DD/MM/YYYY'
SITE_NAME = 'AAP Newsroom'
COPYRIGHT_HOLDER = 'AAP'
COPYRIGHT_NOTICE = ''
USAGE_TERMS = ''
