from superdesk.core.module import Module
from .views import aap_rss_endpoints

module = Module(name="newsroom.news_api.aaprss", endpoints=[aap_rss_endpoints])
