import os
import pathlib

from quart_babel import lazy_gettext

from newsroom.web.default_settings import CLIENT_CONFIG

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

WIRE_AGGS = {
    "genre": {"terms": {"field": "genre.name", "size": 50}},
    "service": {"terms": {"field": "service.name", "size": 50}},
    "subject": {"terms": {"field": "subject.name", "size": 100}},
    "urgency": {"terms": {"field": "urgency"}},
    "place": {"terms": {"field": "place.name", "size": 50}},
}

WIRE_SECTION = lazy_gettext("The Wire")

CLIENT_CONFIG.update({
    "list_animations": False,
})
