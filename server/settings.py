import os
import pathlib
from quart_babel import lazy_gettext

from newsroom.search.service import strtobool
from newsroom.web.default_settings import (
    CLIENT_CONFIG,
    BLUEPRINTS as blueprints,
    CORE_APPS,
)

if os.environ.get("PUSH"):
    BLUEPRINTS = blueprints
else:
    BLUEPRINTS = [blueprint for blueprint in blueprints if "push" not in blueprint]

BLUEPRINTS.append("newsroom.market_place")
BLUEPRINTS.append("newsroom.media_releases")
BLUEPRINTS.append("aap_public")
BLUEPRINTS.append("newsroom.factcheck")

SERVER_PATH = pathlib.Path(__file__).resolve().parent
CLIENT_PATH = SERVER_PATH.parent.joinpath("client")

WEBPACK_MANIFEST_PATH = os.environ.get(
    "WEBPACK_MANIFEST_PATH", CLIENT_PATH.joinpath("dist", "manifest.json")
)

CONTACT_ADDRESS = "https://www.aap.com.au/contact"
SITE_NAME = "AAP Newsroom"
COPYRIGHT_HOLDER = "AAP"
COPYRIGHT_NOTICE = ""
USAGE_TERMS = ""
LANGUAGES = ["en"]
DEFAULT_LANGUAGE = "en"
PRIVACY_POLICY = "https://www.aap.com.au/legal/"
TERMS_AND_CONDITIONS = "https://www.aap.com.au/legal/"
SHOW_COPYRIGHT = True

WIRE_AGGS = {
    "genre": {"terms": {"field": "genre.name", "size": 50}},
    "service": {"terms": {"field": "service.name", "size": 50}},
    "subject": {"terms": {"field": "subject.name", "size": 100}},
    "urgency": {"terms": {"field": "urgency"}},
    "place": {"terms": {"field": "place.name", "size": 50}},
}

WATERMARK_IMAGE = os.environ.get(
    "WATERMARK_IMAGE", os.path.join(os.path.dirname(__file__), "theme", "watermark.png")
)

WIRE_SECTION = lazy_gettext("The Wire")

FACTCHECK_WEBSITE_URL = os.environ.get(
    "FACTCHECK_WEBSITE_URL", "https://www.aap.com.au/factcheck/"
)
MULTIMEDIA_WEBSITE_URL = os.environ.get(
    "MULTIMEDIA_WEBSITE_URL", "https://photos.aap.com.au"
)
MULTIMEDIA_WEBSITE_SEARCH_URL = "{}/{}/".format(
    MULTIMEDIA_WEBSITE_URL, os.environ.get("MULTIMEDIA_WEBSITE_SEARCH_PATH", "search")
)
EXPLAINERS_WEBSITE_URL = os.environ.get(
    "EXPLAINERS_WEBSITE_URL",
    "https://photos.aap.com.au/search/(supplementalcategory"
    ":VIDEXP)/Visual%20Explainers",
)
AAP_PHOTOS_TOKEN = os.environ.get("AAP_PHOTOS_TOKEN", None)
ALLOW_PICTURE_DOWNLOAD = False
MONITORING_REPORT_NAME = "Newswire"
PLYR = True
EMBED_PRODUCT_FILTERING = strtobool(os.environ.get("EMBED_PRODUCT_FILTERING", "true"))

CLIENT_CONFIG.update(
    {
        "multimedia_website_search_url": MULTIMEDIA_WEBSITE_SEARCH_URL,
        "display_all_versions_toggle": False,
        "list_animations": False,
    }
)
CLIENT_CONFIG["locale_formats"]["en"]["DATE_FORMAT_HEADER"] = "EEEE, MMMM d, yyyy"

# We want the section filter to be last
# So we remove it from CORE_APPS and place after
# aapX/Media Releases etc
if "newsroom.news_api" in CORE_APPS:
    CORE_APPS.remove("newsroom.news_api")

INSTALLED_APPS = [
    "aap.external_products",
    "aap.photos",
    "releases",
    "newsroom.market_place",
    "newsroom.factcheck",
    "newsroom.media_releases",
    "newsroom.news_api",
]

NEWS_API_ENABLED = strtobool(os.environ.get("NEWS_API_ENABLED", "false"))
ALLOW_PICTURE_DOWNLOAD = strtobool(os.environ.get("ALLOW_PICTURE_DOWNLOAD", "false"))
WIRE_EMBED_PERMISSIONS = strtobool(os.environ.get("WIRE_EMBED_PERMISSIONS", "true"))
USE_EMBED_PERMISSIONS_IN_DASHBOARD = strtobool(
    os.environ.get("WIRE_EMBED_PERMISSIONS", "false")
)

WIRE_TIME_FILTERS = []

PERMISSION_DASHBOARD_CARDS = True
