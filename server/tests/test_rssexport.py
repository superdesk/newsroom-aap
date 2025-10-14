from datetime import timedelta
import xml.etree.ElementTree as ET

from superdesk.utc import utcnow
from newsroom.tests.test_utils import create_entries_for, delete_entries_for
from aap.commands.rssexport import RSSExport


async def test_rssexport(app, tmp_path):
    print(tmp_path)
    now = utcnow()
    start = (now - timedelta(days=2)).strftime("%Y-%m-%d")
    end = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    items = [
        {
            "_id": "urn:test:11111",
            "_updated": now - timedelta(days=1),
            "versioncreated": now - timedelta(days=1),
            "firstpublished": now - timedelta(days=1),
            "pubstatus": "usable",
            "headline": "Test Headline",
            "body_html": "<p>Test Body</p>",
            "source": "AAP",
        },
    ]
    company = [{"_id": "65243c22e431206126f582d9", "name": "test"}]

    app.config["ELASTIC_DATETIME_FORMAT"] = "%Y-%m-%dT%H:%M:%S"
    app.config["QUERY_MAX_PAGE_SIZE"] = 100
    app.config["NEWSAPI_URL"] = "http://localhost:"

    await delete_entries_for("items")
    await create_entries_for("items", items)
    await create_entries_for("companies", company)

    company_id = "65243c22e431206126f582d9"

    rss = RSSExport(company_id, tmp_path, start, end)
    await rss.run()

    rss_file = (
        tmp_path
        / f"{(now - timedelta(days=1)).strftime('%Y')}"
        / f"feed-{(now - timedelta(days=1)).strftime('%Y-%m-%d')}"
    )
    tree = ET.parse(str(rss_file))
    root = tree.getroot()
    assert root.tag == "rss"

    channel = root.find("channel")
    assert channel is not None, "A <channel> element must exist"

    item = channel.find("item")
    assert item is not None, "At least one <item> element must exist in the channel"

    title = item.find("title")
    assert title is not None, "<item> must have a <title>"
    assert title.text == "Test Headline"

    link = item.find("link")
    assert link is not None, "<item> must have a <link>"
    assert link.text == "https://aapnews.com.au/news/test-headline"
