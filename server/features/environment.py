from newsroom.tests.news_api.environment import before_all, before_scenario  # noqa
from newsroom.news_api.default_settings import MODULES

MODULES.extend(["aap.aaprss"])
