from lxml.html import HtmlElement
from newsroom.formatters import BaseFormatter, FormatterAssetType
from quart_babel import lazy_gettext
from newsroom.wire.formatters.utils import log_media_downloads
from newsroom.news_api.utils import (
    remove_internal_renditions,
)
from newsroom.utils import update_embeds_in_body
from newsroom.wire.formatters.utils import remove_unpermissioned_embeds
from superdesk.logging import logger
from superdesk.flask import render_template
from newsroom.types import SectionEnum, Any, List


class HTMLPackageFormatter(BaseFormatter):
    FILE_EXTENSION = "html"
    MIMETYPE = "application/zip"
    format_id = "html_package"
    name = lazy_gettext("HTML package")
    sections = [
        SectionEnum.WIRE,
        SectionEnum.FACTCHECK,
        SectionEnum.MONITORING,
        SectionEnum.MARKET_PLACE,
        SectionEnum.MEDIA_RELEASES,
    ]
    assets = [FormatterAssetType.TEXT]
    MULTI_ZIP = True

    @staticmethod
    def rewire_embeded_images(item: dict[str, Any]) -> None:
        def _get_source_ref(marker: str, item: dict[str, Any]) -> str:
            widest: int = -1
            src_rendition: str = ""
            renditions: dict[str, Any] = (
                item.get("associations", {}).get(marker, {}).get("renditions", [])
            )
            for rendition in renditions:
                width: int = (
                    item.get("associations", {})
                    .get(marker, {})
                    .get("renditions", {})
                    .get(rendition, {})
                    .get("width", -2)
                )
                if width > widest:
                    widest = width
                    src_rendition = rendition

            if widest > 0:
                return (
                    item.get("associations", {})
                    .get(marker, {})
                    .get("renditions", {})
                    .get(src_rendition, {})
                    .get("href", "")
                    .lstrip("/")
                )

            logger.warning("href not found for the original in HTMLPackage formatter")
            return ""

        def _get_source_set_refs(marker: str, item: dict[str, Any]) -> str:
            """
            For the given marker (association) return the set of available hrefs and the widths
            :param marker:
            :param item:
            :return:
            """
            srcset = []
            renditions: List[dict[str, Any]] = (
                item.get("associations", {}).get(marker, {}).get("renditions", {})
            )
            for rendition in renditions:
                ref = (
                    item.get("associations", {})
                    .get(marker, {})
                    .get("renditions", {})
                    .get(rendition, {})
                    .get("href", "")
                    .lstrip("/")
                )
                srcset.append(
                    ref
                    + " "
                    + str(
                        item.get("associations", {})
                        .get(marker, {})
                        .get("renditions", {})
                        .get(rendition, {})
                        .get("width", "")
                    )
                    + "w"
                )
            return ",".join(srcset)

        def update_image(item: dict[str, Any], elem: HtmlElement, group: str) -> bool:
            embed_id: str = "editor_" + group
            elem.attrib["id"] = embed_id
            src: str = _get_source_ref(embed_id, item)
            if src:
                elem.attrib["src"] = src
            srcset: str = _get_source_set_refs(embed_id, item)
            if srcset:
                elem.attrib["srcset"] = srcset
                elem.attrib["sizes"] = "80vw"
            return True

        def update_video_or_audio(item, elem, group) -> bool:
            embed_id = "editor_" + group
            elem.attrib["id"] = embed_id
            elem.attrib["src"] = (
                item.get("associations")
                .get(embed_id)
                .get("renditions")
                .get("original")
                .get("href")
                .lstrip("/")
            )
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
        Set the references in the feature media strip the leading / to make it a legitimate relative path
        :param item:
        :return:
        """
        renditions = (
            item.get("associations", {}).get("featuremedia", {}).get("renditions", {})
        )
        for _rendition_key, rendition_data in renditions.items():
            rendition_data["href"] = rendition_data.get("href", "").lstrip("/")

    async def format_item(
        self, item: dict[str, Any], item_type: str | None = "items"
    ) -> bytes:
        await remove_unpermissioned_embeds(item)
        remove_internal_renditions(item, remove_media=False)
        self.rewire_embeded_images(item)
        self.rewire_featuremedia(item)
        await log_media_downloads(item)
        return str.encode(
            await render_template("download_embed.html", item=item), "utf-8"
        )
