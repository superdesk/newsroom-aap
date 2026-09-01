from superdesk.core.web import EndpointGroup
from superdesk.core.types import Request, Response

from aap.formatters.aaprss import AAPRSSFormatter
from aap.formatters.types import RSSParams
from newsroom.news_api.api_tokens.auth import support_auth_token_in_url
from newsroom.news_api.news.rss.views import RSSArgs

aap_rss_endpoints = EndpointGroup("aaprss", __name__)


@aap_rss_endpoints.endpoint("aap-rss", title="AAP RSS (Header auth)", methods=["GET"])
async def get_rss_authed(args: None, params: RSSParams, request: Request) -> Response:
    return await AAPRSSFormatter().format_feed(params, None, request)


@aap_rss_endpoints.endpoint(
    "aap-rss/<path:token>",
    title="AAP RSS Feed (URL auth)",
    methods=["GET"],
    auth=[support_auth_token_in_url],
)
async def get_rss_token(args: RSSArgs, params: RSSParams, request: Request) -> Response:
    return await AAPRSSFormatter().format_feed(params, args, request)
