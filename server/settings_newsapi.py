import os
from pathlib import Path

from superdesk.default_settings import env, strtobool  # noqa
from newsroom.news_api.default_settings import (
    CORE_APPS,
    INSTALLED_APPS,
    BLUEPRINTS,
    MODULES,
)


ABS_PATH = Path(__file__).resolve().parent

# extend apps
CORE_APPS.extend([])
INSTALLED_APPS.extend([])
BLUEPRINTS.extend([])
MODULES.extend(["aap.aaprss"])

NEWS_API_ENABLED = strtobool(os.environ.get("NEWS_API_ENABLED", "false"))
COPYRIGHT_HOLDER = "AAP"
API_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S+0000"
SITE_NAME = "AAP Newsroom"
