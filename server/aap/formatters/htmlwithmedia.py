import flask
from lxml.html import HtmlElement
from newsroom.types import Any
from quart_babel import lazy_gettext
from superdesk.flask import render_template
from newsroom.formatters import BaseFormatter, FormatterAssetType
from newsroom.wire.formatters.utils import (
    log_media_downloads,
    remove_unpermissioned_embeds,
)
from newsroom.news_api.utils import (
    remove_internal_renditions,
)
from newsroom.utils import update_embeds_in_body
from newsroom.assets import ASSETS_RESOURCE
from newsroom.types import SectionEnum
import base64


class HTMLMediaFormatter(BaseFormatter):
    """
    This formatter will render an HTML file with the media embedded as base64 encoded strings
    """

    FILE_EXTENSION = "html"
    MIMETYPE = "text/html"
    format_id = "html_media"
    name = lazy_gettext("HTML with embedded media")
    sections = [
        SectionEnum.WIRE,
        SectionEnum.FACTCHECK,
        SectionEnum.MONITORING,
        SectionEnum.MARKET_PLACE,
        SectionEnum.MEDIA_RELEASES,
    ]
    assets = [FormatterAssetType.TEXT]

    @staticmethod
    def get_base64image(embed_id: str, item: dict[str, Any]) -> str:
        widest = -1
        src_rendition = ""
        renditions = item.get("associations", {}).get(embed_id).get("renditions", [])
        for rendition in renditions:
            width = (
                item.get("associations", {})
                .get(embed_id)
                .get("renditions", {})
                .get(rendition)
                .get("width", -2)
            )
            if width > widest:
                widest = width
                src_rendition = rendition

        src = (
            item.get("associations", {})
            .get(embed_id, {})
            .get("renditions", {})
            .get(src_rendition)
            .get("media", "")
        )
        mimetype = (
            item.get("associations", {})
            .get(embed_id, {})
            .get("renditions", {})
            .get(src_rendition, {})
            .get("mimetype", "")
        )
        file = flask.current_app.media.get(src, ASSETS_RESOURCE)
        b64 = (
            "data:{};base64,".format(mimetype) + base64.b64encode(file.read()).decode()
        )
        return b64

    @staticmethod
    def get_base64href(embed_id: str, item: dict[str, Any]) -> str:
        src = (
            item.get("associations", {})
            .get(embed_id, {})
            .get("renditions", {})
            .get("original", {})
            .get("media", "")
        )
        mimetype = (
            item.get("associations", {})
            .get(embed_id, {})
            .get("renditions", {})
            .get("original", {})
            .get("mimetype", "")
        )
        file = flask.current_app.media.get(src, ASSETS_RESOURCE)
        b64 = (
            "data:{};base64,".format(mimetype) + base64.b64encode(file.read()).decode()
        )
        return b64

    def rewire_embedded_images(self, item: dict[str, Any]) -> None:
        def update_image(item: dict[str, Any], elem: HtmlElement, group: str) -> bool:
            embed_id: str = "editor_" + group
            elem.attrib["id"] = embed_id
            src = self.get_base64image(embed_id, item)
            if src:
                elem.attrib["src"] = src
            return True

        def update_video_or_audio(
            item: dict[str, Any], elem: HtmlElement, group: str
        ) -> bool:
            embed_id: str = "editor_" + group
            elem.attrib["id"] = embed_id
            src = self.get_base64href(embed_id, item)
            if src:
                elem.attrib["src"] = src
            elem.attrib.pop("alt", None)
            elem.attrib.pop("width", None)
            elem.attrib.pop("height", None)
            return True

        update_embeds_in_body(
            item, update_image, update_video_or_audio, update_video_or_audio
        )

    @staticmethod
    def rewire_featuremedia(item: dict[str, Any]) -> None:
        """
        Set the references in the feature media to base64 encoded versions
        :param item:
        :return:
        """
        renditions = (
            item.get("associations", {}).get("featuremedia", {}).get("renditions", [])
        )
        for rendition in renditions:
            src: str = (
                item.get("associations", {})
                .get("featuremedia", {})
                .get("renditions", {})
                .get(rendition)
                .get("media", "")
            )
            mimetype: str = (
                item.get("associations", {})
                .get("featuremedia", {})
                .get("renditions", {})
                .get(rendition)
                .get("mimetype", "")
            )
            file = flask.current_app.media.get(src, ASSETS_RESOURCE)
            if file and mimetype:
                item["associations"]["featuremedia"]["renditions"][rendition][
                    "href"
                ] = (
                    "data:{};base64,".format(mimetype)
                    + base64.b64encode(file.read()).decode()
                )

    async def format_item(
        self, item: dict[str, Any], item_type: str | None = "items"
    ) -> bytes:
        await remove_unpermissioned_embeds(item)
        remove_internal_renditions(item)
        self.rewire_embedded_images(item)
        self.rewire_featuremedia(item)
        resp = str.encode(
            await render_template("download_embed.html", item=item), "utf-8"
        )
        # log media as the last step in case something fails!
        await log_media_downloads(item)
        return resp
