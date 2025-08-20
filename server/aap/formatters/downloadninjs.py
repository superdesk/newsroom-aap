from lxml.html import HtmlElement
from newsroom.formatters import FormatterAssetType
from quart_babel import lazy_gettext
from superdesk.logging import logger
from newsroom.wire.formatters.ninjs import NINJSFormatter
from newsroom.wire.formatters.utils import (
    log_media_downloads,
    remove_unpermissioned_embeds,
)
from newsroom.news_api.utils import (
    remove_internal_renditions,
)
from newsroom.utils import update_embeds_in_body
from newsroom.types import SectionEnum, Any


class NINJSDownloadFormatter(NINJSFormatter):
    """
    Overload the NINJSFormatter and add the associations as a field to copy
    """

    FILE_EXTENSION = "json"
    MIMETYPE = "application/zip"
    format_id = "ninjspackage"
    name = lazy_gettext("NINJS package")
    sections = [
        SectionEnum.WIRE,
        SectionEnum.FACTCHECK,
        SectionEnum.MONITORING,
        SectionEnum.MARKET_PLACE,
        SectionEnum.MEDIA_RELEASES,
    ]
    assets = [FormatterAssetType.TEXT]
    MULTI_ZIP = True

    def __init__(self):
        self.direct_copy_properties += ("associations",)

    @staticmethod
    def rewire_embeded_images(item: dict[str, Any]) -> None:
        def _get_source_ref(marker: str, item: dict[str, Any]):
            widest = -1
            src_rendition = ""
            renditions = (
                item.get("associations", {}).get(marker, {}).get("renditions", [])
            )
            for rendition in renditions:
                width = (
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

            logger.warning(
                "href not found for the original in " "NINJSDownload formatter"
            )
            return None

        def _get_source_set_refs(marker: str, item: dict[str, Any]) -> str:
            """
            For the given marker (association) return the set
            of available hrefs and the widths
            :param marker:
            :param item:
            :return:
            """
            srcset = []
            for rendition in (
                item.get("associations", {}).get(marker, {}).get("renditions", [])
            ):
                srcset.append(
                    item.get("associations", {})
                    .get(marker)
                    .get("renditions", {})
                    .get(rendition, {})
                    .get("href", "")
                    .lstrip("/")
                    + " "
                    + str(
                        item.get("associations", {})
                        .get(marker)
                        .get("renditions", {})
                        .get(rendition, {})
                        .get("width", "")
                    )
                    + "w"
                )
            return ",".join(srcset)

        def update_image(item: dict[str, Any], elem: HtmlElement, group: str) -> bool:
            embed_id = "editor_" + group
            elem.attrib["id"] = embed_id
            src = _get_source_ref(embed_id, item)
            if src:
                elem.attrib["src"] = src
            srcset = _get_source_set_refs(embed_id, item)
            if srcset:
                elem.attrib["srcset"] = srcset
                elem.attrib["sizes"] = "80vw"
            return True

        def update_video_or_audio(
            item: dict[str, Any], elem: HtmlElement, group: str
        ) -> bool:
            embed_id = "editor_" + group
            elem.attrib["id"] = embed_id
            # cleanup the element to ensure the html will validate
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
        Set the references in the feature media strip the leading / to
        make it a legitimate relative path
        :param item
        :return None
        """
        renditions = (
            item.get("associations", {}).get("featuremedia", {}).get("renditions", {})
        )
        for _rendition_key, rendition_data in renditions.items():
            rendition_data["href"] = rendition_data.get("href", "").lstrip("/")

    async def _transform_to_ninjs(self, item: dict[str, Any]):
        await remove_unpermissioned_embeds(item)
        # Remove the renditions we should not be showing the world
        remove_internal_renditions(item, remove_media=False)
        # set the references embedded in the html body of the story
        self.rewire_embeded_images(item)
        self.rewire_featuremedia(item)
        resp = await super()._transform_to_ninjs(item)
        await log_media_downloads(item)
        return resp
