#!/usr/bin/env python
import os
from dataclasses import dataclass
from lxml import etree
from lxml.etree import Element, SubElement
import logging
import zipfile

import click
from datetime import date, timedelta, datetime

from superdesk import get_app_config
from newsroom.commands.cli import newsroom_cli
from newsroom.news_api.news.search_service import NewsApiSearchServiceAsync
from newsroom.news_api.news.types import NewsApiSearchRequestArgs
from newsroom.search.types import NewshubSearchRequest
from newsroom.companies import CompanyServiceAsync
from newsroom.news_api.app import get_app
from aap.formatters.aaprss import AAPRSSFormatter
from newsroom.wire.embeds import remove_all_embeds

logger = logging.getLogger(__name__)


@dataclass
class RSSExport(AAPRSSFormatter):
    company_id: str
    output_dir: str
    start: str
    end: str
    public_url: str
    zip: bool = False
    include_kills: bool = True

    def get_root_xml(self) -> tuple[Element, Element]:
        feed = Element("rss", attrib={"version": "2.0"}, nsmap=self.nsmap)
        channel = SubElement(feed, "channel")
        title = self.get_title()
        SubElement(channel, "title").text = title
        SubElement(channel, "description").text = title
        # No adapter is defined!!!
        # SubElement(channel, "link").text = url_for("aaprss.get_rss_authed", _external=True)
        SubElement(channel, "link").text = (
            get_app_config("NEWSAPI_URL")
            + "/"
            + get_app_config("URL_PREFIX")
            + "/aaprss"
        )

        return feed, channel

    def write_to_file(self, xml_content, export_date, output_dir, zip_enabled):
        """
        Write the content to file, possibly compressed
        :param xml_content:
        :param export_date:
        :param output_dir:
        :param zip_enabled:
        :return:
        """
        output_path: str = os.path.join(output_dir, export_date.strftime("%Y"))
        os.makedirs(output_path, exist_ok=True)

        file_name = "feed-" + export_date.strftime("%Y-%m-%-d")
        try:
            if zip_enabled:
                zip_path = os.path.join(output_path, file_name.replace(".xml", ".zip"))
                with zipfile.ZipFile(
                    zip_path, mode="w", compression=zipfile.ZIP_DEFLATED
                ) as zf:
                    zf.writestr(file_name, xml_content)
            else:
                file_path = os.path.join(output_path, file_name)
                with open(file_path, "w", encoding="utf-8") as fp:
                    fp.write(xml_content)
        except Exception as e:
            logger.exception(f"Failed to write output file {file_name}: {e}")
            raise

    async def process_day_of_docs(self, docs, export_date):
        """
        Process a days worth of content
        :param docs:
        :param export_date:
        :return:
        """
        feed, channel = self.get_root_xml()
        # Get the complete record for each item returned by the search from mongo
        db_docs = await super().get_db_docs(docs)
        # get the first versions
        original_docs = await super().get_original_docs(db_docs)

        for item in docs:
            try:
                complete_item = db_docs.get(item.get("_id"))
                if not complete_item:
                    logger.warning(
                        "mongo entry not found for {}".format(item.get("_id"))
                    )
                    continue

                # Ignore kills in initial bulk run
                if not item.get("pubstatus") == "usable" and not self.include_kills:
                    continue

                original_item = await super().get_original_item(
                    complete_item, original_docs
                )
                if original_item:
                    item["original_headline"] = original_item.get("headline", None)

                remove_all_embeds(complete_item)
                complete_item.pop("associations", None)

                entry = SubElement(channel, self.item_field)
                await super().format_item(entry, complete_item, None)

            except Exception as ex:
                logger.exception("processing {} - {}".format(item.get("_id"), ex))

        self.write_to_file(
            etree.tostring(
                feed,
                method="xml",
                pretty_print=True,
                xml_declaration=True,
                encoding="UTF-8",
            ).decode("utf-8"),
            export_date,
            self.output_dir,
            self.zip,
        )

    def parse_date(self, date_str: str, var_name: str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            print(
                f"Error: Invalid {var_name} format. Please use YYYY-MM-DD. Received: {date_str}"
            )
            return None

    async def run(self):
        parsed_start_date = self.parse_date(self.start, "start_date")
        if parsed_start_date is None:
            return

        parsed_end_date = self.parse_date(self.end, "end_date")
        if parsed_end_date is None:
            return

        if parsed_start_date > parsed_end_date:
            print("Start date must be before end date")
            return

        print(
            f"Processing AAP-RSS between {parsed_start_date.isoformat()} and {parsed_end_date.isoformat()}"
        )
        company_service = CompanyServiceAsync()
        company = await company_service.find_by_id(self.company_id)
        search_service = NewsApiSearchServiceAsync()

        # take each day at a time
        working_day = parsed_start_date

        while working_day <= parsed_end_date:
            print(f"Processing {working_day.isoformat()}")
            docs = []
            page = 1

            while True:
                search_args = NewsApiSearchRequestArgs(
                    page_size=100,
                    page=page,
                    aggs=False,
                    start_date=f"{working_day.isoformat()}T00:00:00",
                    end_date=f"{working_day.isoformat()}T23:59:59",
                )

                results = await search_service.search(
                    NewshubSearchRequest(company=company, args=search_args)
                )
                current_page_docs = await results.to_list_raw()
                if not current_page_docs:
                    break

                docs.extend(current_page_docs)
                page += 1

            if docs:
                print(f"Adding {len(docs)} articles")
                await self.process_day_of_docs(docs, working_day)

            working_day = working_day + timedelta(days=1)


@newsroom_cli.command("rssexport")
@click.option(
    "-s",
    "--start_date",
    default=(date.today() - timedelta(days=1)).isoformat(),
    help="Start date in the form YYYY-MM-DD for the export",
)
@click.option(
    "-e",
    "--end_date",
    default=date.today().isoformat(),
    help="End date for the export in YYYY-MM-DD inclusive",
)
@click.option(
    "-c",
    "--company_id",
    default=None,
    required=True,
    help="A string version of the company id whose permissions will be applied",
)
@click.option(
    "-o",
    "--output_dir",
    default=None,
    required=True,
    help="The Directory the output will be written to",
)
@click.option(
    "-u",
    "--url",
    default="https://aapnews.com.au/news",
    help='The URL that the items will reference, defaults to "https://aapnews.aap.com.au/news"',
)
@click.option(
    "-z",
    "--zip",
    default=False,
    is_flag=True,
    help="Indicates if the output files should be compressed",
)
@click.option(
    "-k",
    "--kills",
    default=True,
    is_flag=True,
    help="True|False if kills are included in output, defaults to True",
)
async def rss_export(company_id, output_dir, start_date, end_date, zip, url, kills):
    print("AAP RSS export starting")
    get_app()
    rs = RSSExport(
        company_id=company_id,
        output_dir=output_dir,
        start=start_date,
        end=end_date,
        public_url=url,
        zip=zip,
        include_kills=kills,
    )
    await rs.run()
    print("Finished")
