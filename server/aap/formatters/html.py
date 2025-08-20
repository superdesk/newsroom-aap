from typing import Any

from newsroom.formatters import BaseFormatter, FormatterAssetType
from quart_babel import lazy_gettext
from newsroom.types import SectionEnum
from superdesk.flask import render_template
from newsroom.utils import remove_all_embeds


class HTMLFormatter(BaseFormatter):
    """
    Formatter that allows the download of "plain" html
    with any embeds in the html body stripped
    """

    format_id = "html"
    name = lazy_gettext("Plain HTML")
    sections = [
        SectionEnum.WIRE,
        SectionEnum.FACTCHECK,
        SectionEnum.MONITORING,
        SectionEnum.MARKET_PLACE,
        SectionEnum.MEDIA_RELEASES,
    ]
    assets = [FormatterAssetType.TEXT]

    FILE_EXTENSION = "html"
    MIMETYPE = "text/html"

    async def format_item(
        self, item: dict[str, Any], item_type: str | None = "items"
    ) -> bytes:
        remove_all_embeds(item)
        return str.encode(
            await render_template("download_item.html", item=item), "utf-8"
        )
