
import os
from newsroom.default_settings import BLUEPRINTS as blueprints, CORE_APPS, CLIENT_CONFIG

if os.environ.get('PUSH'):
    BLUEPRINTS = blueprints
else:
    BLUEPRINTS = [blueprint for blueprint in blueprints if 'push' not in blueprint]

BLUEPRINTS.append('newsroom.am_news')
BLUEPRINTS.append('newsroom.market_place')
BLUEPRINTS.append('newsroom.media_releases')
BLUEPRINTS.append('aap_public')


# We want the section filter to be last
# So we remove it from CORE_APPS and place after
# aapX/Media Releases etc
if 'newsroom.news_api' in CORE_APPS:
    CORE_APPS.remove('newsroom.news_api')

INSTALLED_APPS = [
    'instrumentation',
    'photos',
    'newsroom.am_news',
    'newsroom.market_place',
    'newsroom.media_releases',
    'newsroom-defaults',
    'newsroom.news_api',
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
FACTCHECK_WEBSITE_URL = os.environ.get('FACTCHECK_WEBSITE_URL', 'https://www.aap.com.au/category/factcheck/')
CLIENT_CONFIG['list_animations'] = False
CLIENT_CONFIG['multimedia_website_search_url'] = MULTIMEDIA_WEBSITE_SEARCH_URL
BACK_STORY_URL = os.environ.get('BACK_STORY_URL', 'https://backstory.aap.com.au/')
ALLOW_PICTURE_DOWNLOAD = False

MONITORING_REPORT_NAME = 'Newswire'
