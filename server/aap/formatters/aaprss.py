from datetime import datetime
import logging
import re
import unicodedata
from typing import List, Any
from urllib.parse import urljoin, urlparse
from motor.motor_asyncio import AsyncIOMotorCollection

from email.utils import format_datetime

from lxml import etree
from lxml.etree import Element, SubElement, QName

from superdesk.core import get_app_config
from superdesk.core.types import Request, Response
from superdesk.flask import url_for

from newsroom.news_api.formatters import RSSFormatter
from newsroom.news_api.news.rss.views import RSSArgs
from newsroom.news_api.news.types import NewsApiSearchRequestArgs
from newsroom.types import SectionEnum
from newsroom.wire import WireSearchServiceAsync
from newsroom.wire.embeds import apply_company_permissions_to_embeds, update_embed_urls
from newsroom.news_api.news.search_service import NewsApiSearchServiceAsync
from aap.formatters.types import RSSParams

logger = logging.getLogger(__name__)


class AAPRSSFormatter(RSSFormatter):
    name: str = "AAP RSS Feed"
    mimetype: str = "application/rss+xml; charset=utf-8"
    nsmap: dict = {
        "content": "http://purl.org/rss/1.0/modules/content/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "dcterms": "http://purl.org/dc/terms/",
        "licensed_news": "https://www.google.com/schemas/rss-licensed-news/",
        "media": "http://search.yahoo.com/mrss/",
    }
    item_field: str = "item"
    item_id_field: str = "id"
    public_url = "https://aapnews.aap.com.au/news/"

    async def get_db_docs(self, items: List[dict[str, Any]]) -> dict[str, Any]:
        """
        Given the docs found by the search, we get the complete version from mongo.
        :param items:
        :return: List of documents from mongo
        """
        wire_service = WireSearchServiceAsync().service
        cursor = await wire_service.search(
            {"_id": {"$in": [d.get("_id") for d in items]}}, use_mongo=True
        )
        return {i.id: i.to_dict() async for i in cursor}

    async def get_original_docs(self, db_docs: dict[str, Any]) -> dict[str, Any]:
        """
        find the id's of the original published version as the canonical URL is set by the headline of the 1st version
        :param db_docs:
        :return:
        """
        original_ids = []
        for db_doc in db_docs.values():
            if db_doc.get("ancestors"):
                original_id = (
                    db_doc.get("ancestors")[0]
                    if len(db_doc.get("ancestors")) >= 1
                    else None
                )
                if original_id:
                    original_ids.append(original_id)

        wire_service = WireSearchServiceAsync().service
        cursor = await wire_service.search(
            {"_id": {"$in": original_ids}}, use_mongo=True
        )
        return {i.id: i.to_dict() async for i in cursor}

    async def get_original_item(
        self, complete_item: dict, original_docs: dict[str, Any]
    ) -> dict | None:
        """
        Given an item, try to find the original version in the original_docs, there is a special case for
        items that have been corrected, killed or taken down but have only a single version, in that case we need to
        look it up in the items_versions collection
        :param complete_item:
        :param original_docs:
        :return:
        """
        original_item = None
        ancestors = complete_item.get("ancestors")
        if ancestors:
            original_item = original_docs.get(ancestors[0])
            if not original_item:
                logger.error(
                    "original_item not found for {}".format(complete_item.get("_id"))
                )
        else:  # handle the kills, takedowns and corrections, they should not be that common
            if not complete_item.get("pubstatus") == "usable" or not complete_item.get(
                "firstpublished"
            ) == complete_item.get("versioncreated"):
                wire_service = WireSearchServiceAsync().service
                collection: AsyncIOMotorCollection = wire_service.mongo_versioned_async

                original_item = await collection.find_one(
                    {"_id_document": complete_item.get("_id")},
                    sort=[("_current_version", 1)],
                )
                if not original_item:
                    logger.warning(
                        "no original version found for killed/corrected item {}".format(
                            complete_item.get("_id")
                        )
                    )
        return original_item

    async def format_item(
        self, entry: SubElement, item: dict, token: str | None
    ) -> None:
        self.set_item_details(entry, item)
        self.set_item_state(entry, item)
        await update_embed_urls(item, token)
        self.set_item_content(entry, item)

        try:
            if item["associations"]["featuremedia"]["renditions"]:
                self.set_item_featuremedia_details(
                    entry,
                    item["associations"]["featuremedia"],
                    token=token,
                    item_id=item.get("_id"),
                )
        except (KeyError, TypeError):
            pass

    def get_root_xml(self) -> tuple[Element, Element]:
        feed = Element("rss", attrib={"version": "2.0"}, nsmap=self.nsmap)
        channel = SubElement(feed, "channel")
        title = self.get_title()
        SubElement(channel, "title").text = title
        SubElement(channel, "description").text = title
        SubElement(channel, "link").text = url_for(
            "aaprss.get_rss_authed", _external=True
        )

        return feed, channel

    async def format_feed(
        self, params: RSSParams | None, args: RSSArgs | None, request: Request
    ) -> Response:
        xml_root: str = '<?xml version="1.0" encoding="UTF-8"?>'
        feed, channel = self.get_root_xml()

        docs: List[dict] = []
        search_service = NewsApiSearchServiceAsync()
        search_args = NewsApiSearchRequestArgs()
        search_args.page_size = 100
        search_args.page = 1
        while True:
            search_args.start_date = (
                f"now-{params.days}d"
                if params is not None and params.days
                else "now-2d"
            )

            results = await search_service.search(search_args)
            current_page_docs = await results.to_list_raw()

            if not current_page_docs:
                break
            docs.extend(current_page_docs)
            search_args.page += 1

        complete_items: dict[str, Any] = await self.get_db_docs(docs)
        original_docs: dict[str, Any] = await self.get_original_docs(complete_items)

        for item in docs:
            try:
                complete_item = complete_items.get(item.get("_id", "not found"))
                if not complete_item:
                    continue

                original_item = await self.get_original_item(
                    complete_item, original_docs
                )
                if original_item:
                    complete_item["original_headline"] = original_item.get(
                        "headline", None
                    )

                await apply_company_permissions_to_embeds(
                    [complete_item], SectionEnum.NEWS_API
                )
                entry = SubElement(channel, self.item_field)
                await self.format_item(
                    entry, complete_item, getattr(args, "token", None) if args else None
                )

            except Exception as ex:
                logger.exception("processing {} - {}".format(item.get("_id"), ex))
        return Response(
            xml_root
            + etree.tostring(feed, method="xml", pretty_print=True).decode("utf-8"),
            headers=[("Content-Type", self.mimetype)],
        )

    def get_title(self) -> str:
        site_name = get_app_config("SITE_NAME")
        return f"{site_name} RSS Feed"

    def set_item_state(self, entry: SubElement, item: dict) -> None:
        deleted_status = "yes" if not item.get("pubstatus") == "usable" else "no"
        SubElement(
            entry, etree.QName(self.nsmap.get("licensed_news"), "deleted")
        ).text = deleted_status

    def set_item_details(self, entry: SubElement, item: dict) -> None:
        SubElement(entry, "title").text = item.get("headline")

        pubDate = item.get("firstpublished")
        if isinstance(pubDate, datetime):
            SubElement(entry, "pubDate").text = format_datetime(pubDate)
        else:
            # ``firstpublished`` should always have a value, nonetheless log this warning and calm type checkers
            logger.warning(f"No firstpublished date for {item.get('_id')}")

        versioncreated = item.get("versioncreated")
        SubElement(
            entry, QName(self.nsmap.get("dcterms"), "modified")
        ).text = self.format_update_date(versioncreated)
        headline = item.get("original_headline", item.get("headline"))

        # Construct the canonical url that AAP News uses
        text = (
            unicodedata.normalize("NFKD", str(headline))
            .encode("ascii", "ignore")
            .decode("utf-8")
        )
        slug = text.lower()
        slug = re.sub(r"[^\w\s-]", "-", slug)
        slug = re.sub(r"[-\s]+", "-", slug)
        slug = slug.strip("-")

        SubElement(entry, "link").text = urljoin(
            self.public_url,
            (urlparse(self.public_url).path + "/{}".format(slug)).replace("//", "/"),
        )

        if item.get("byline"):
            name = item.get("byline", "")
            if (
                item.get("source")
                and not get_app_config("COPYRIGHT_HOLDER", "").lower()
                == item.get("source", "").lower()
            ):
                name = name + " - " + item.get("source", "")
            SubElement(entry, etree.QName(self.nsmap.get("dc"), "creator")).text = name
        else:
            SubElement(entry, etree.QName(self.nsmap.get("dc"), "creator")).text = (
                item.get("source")
                if item.get("source")
                else get_app_config("COPYRIGHT_HOLDER", "")
            )

        SubElement(entry, "description").text = item.get("description_text", "")
