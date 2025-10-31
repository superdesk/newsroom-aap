from superdesk.core.web import EndpointGroup
from superdesk.core.types import Request, BaseModel, Response

from aap.formatters.aaprss import AAPRSSFormatter

aap_rss_endpoints = EndpointGroup("aaprss", __name__)


class RSSArgs(BaseModel):
    days: int | None = 2


@aap_rss_endpoints.endpoint("aap-rss", methods=["GET"])
async def get_rss_authed(args: None, params: RSSArgs, request: Request) -> Response:
    return await AAPRSSFormatter().format_feed(params, request)
