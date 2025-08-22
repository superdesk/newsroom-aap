import bson
from datetime import timedelta

from zipfile import ZipFile
import lxml.html as lxml_html

from superdesk.core import json
from superdesk.utc import utcnow

from newsroom.tests import test_utils
from newsroom.tests.fixtures import user, auth_users, items, init_items, init_auth  # noqa

items_ids = [item["_id"] for item in items[:2]]
item = items[:2][0]


async def setup_embeds():
    media_id = str(bson.ObjectId())
    associations = {
        "featuremedia": {
            "mimetype": "image/jpeg",
            "type": "picture",
            "products": [{"code": "123", "name": "Product A"}],
            "renditions": {
                "16-9": {
                    "mimetype": "image/jpeg",
                    "href": "http://a.b.c/xxx.jpg",
                    "media": media_id,
                    "width": 1280,
                    "height": 720,
                },
                "4-3": {
                    "href": "/assets/633d11b9fb5122dcf06a6f02",
                    "width": 800,
                    "height": 600,
                    "media": media_id,
                    "mimetype": "image/jpeg",
                },
            },
        },
        "editor_1": {
            "type": "video",
            "renditions": {
                "original": {
                    "mimetype": "video/mp4",
                    "href": "/assets/640ff0bdfb5122dcf06a6fc3",
                    "media": media_id,
                }
            },
            "mimetype": "video/mp4",
            "products": [
                {"code": "123", "name": "Product A"},
                {"code": "321", "name": "Product B"},
            ],
        },
        "editor_0": {
            "type": "audio",
            "renditions": {
                "original": {
                    "mimetype": "audio/mp3",
                    "href": "/assets/640feb9bfb5122dcf06a6f7c",
                    "media": "640feb9bfb5122dcf06a6f7c",
                }
            },
            "mimetype": "audio/mp3",
            "products": [{"code": "999", "name": "NSW News"}],
        },
        "editor_2": {
            "type": "picture",
            "renditions": {
                "4-3": {
                    "href": "/assets/633d11b9fb5122dcf06a6f02",
                    "width": 800,
                    "height": 600,
                    "mimetype": "image/jpeg",
                    "media": "633d11b9fb5122dcf06a6f02",
                },
                "16-9": {
                    "href": "/assets/633d0f59fb5122dcf06a6ee8",
                    "width": 1280,
                    "height": 720,
                    "mimetype": "image/jpeg",
                    "media": "633d0f59fb5122dcf06a6ee8",
                    "poi": {},
                },
            },
            "products": [{"code": "888"}],
        },
        "editor_3": None,
    }
    await test_utils.update_entries_for(
        "items",
        item["_id"],
        {
            "associations": associations,
            "body_html": '<p>Par 1</p><!-- EMBED START Audio {id: "editor_0"} --><figure>'
            '<audio controls src="/assets/640feb9bfb5122dcf06a6f7c" alt="minns" '
            'width="100%" height="100%"></audio>'
            "<figcaption>minns</figcaption>"
            "</figure>"
            '<!-- EMBED END Audio {id: "editor_0"} -->'
            "<p><br></p>"
            "<p>Par 2</p>"
            '<!-- EMBED START Video {id: "editor_1"} -->'
            "<figure>"
            '<video controls src="/assets/640ff0bdfb5122dcf06a6fc3" '
            'alt="Scomo text" width="100%" height="100%">'
            "</video>"
            "<figcaption>Scomo whinging</figcaption>"
            "</figure>"
            '<!-- EMBED END Video {id: "editor_1"} -->'
            "<p><br></p>Par 3<p></p>"
            '<!-- EMBED START Image {id: "editor_2"} -->'
            "<figure>"
            '<img src="/assets/6189e8a48b37621081610714_newsroom_custom" '
            'alt="SCOTT MORRISON MELBOURNE VISIT"'
            ' id="editor_2">'
            "<figcaption>Prime Minister Scott Morrison and Liberal member for "
            "Higgins Katie Allen</figcaption>"
            "</figure>"
            '<!-- EMBED END Image {id: "editor_2"} -->'
            "<p>Par 4</p>",
        },
        item,
    )


def ninjs_content_test(content):
    data = json.loads(content.decode("utf-8"))
    assert data.get("associations").get("editor_1")
    assert not data.get("associations").get("editor_0")
    assert not data.get("associations").get("editor_2")
    assert data.get("headline") == "Amazon Is Opening More Bookstores"
    assert "editor_1" in data.get("body_html")
    assert "editor_0" not in data.get("body_html")


def html_content_test(content):
    root = lxml_html.fromstring(content)
    assert root.tag == "html"


wire_formats = [
    {
        "format": "html",
        "mimetype": "text/html",
        "filename": test_utils.get_download_filename("amazon-bookstore-opening.html", item),
        "test_content": html_content_test,
    },
    {
        "format": "html_media",
        "mimetype": "text/html",
        "filename": test_utils.get_download_filename("amazon-bookstore-opening.html", item),
        "test_content": html_content_test,
    },
]


async def test_ninjs_download(client, app):
    await setup_embeds()
    app.config["EMBED_PRODUCT_FILTERING"] = True
    await test_utils.create_entries_for(
        "companies",
        [
            {
                "_id": "111111111111111111111111",
                "name": "Another Press co.",
                "is_enabled": True,
            }
        ],
    )
    user = await test_utils.find_one_for("users", req=None, first_name="admin")
    assert user
    await test_utils.update_entries_for(
        "users", user["_id"], {"company": "111111111111111111111111"}, user
    )
    await test_utils.create_entries_for(
        "products",
        [
            {
                "_id": "111111111111111111111111",
                "name": "product test",
                "sd_product_id": "123",
                "companies": ["111111111111111111111111"],
                "is_enabled": True,
                "product_type": "wire",
            }
        ],
    )
    app.general_setting("news_api_allowed_renditions", "Foo", default="16-9,4-3")

    _file = await test_utils.download_zip_file(client, items_ids, "ninjspackage", "wire")
    with ZipFile(_file) as zf:
        assert test_utils.get_download_filename("amazon-bookstore-opening.json", item) in zf.namelist()
        content = zf.open(test_utils.get_download_filename("amazon-bookstore-opening.json", item)).read()
    ninjs_content_test(content)
    history = await test_utils.get_all("history")
    assert 4 == len(history)
    assert "download" in history[0]["action"]
    assert "download" in history[1]["action"]
    assert history[0].get("user")
    assert history[0].get("versioncreated") + timedelta(seconds=2) >= utcnow()
    assert history[0].get("item") in items_ids
    assert history[0].get("version")
    assert history[0].get("company") == bson.ObjectId("111111111111111111111111")
    assert history[0].get("section") == "wire"


async def test_html_package_downloads(client, app):
    await setup_embeds()
    app.config["EMBED_PRODUCT_FILTERING"] = True
    await test_utils.create_entries_for(
        "companies",
        [
            {
                "_id": "111111111111111111111111",
                "name": "Another Press co.",
                "is_enabled": True,
            }
        ],
    )
    user = await test_utils.find_one_for("users", req=None, first_name="admin")
    assert user
    await test_utils.update_entries_for(
        "users", user["_id"], {"company": "111111111111111111111111"}, user
    )
    await test_utils.create_entries_for(
        "products",
        [
            {
                "_id": "111111111111111111111111",
                "name": "product test",
                "sd_product_id": "123",
                "companies": ["111111111111111111111111"],
                "is_enabled": True,
                "product_type": "wire",
            }
        ],
    )
    app.general_setting("news_api_allowed_renditions", "Foo", default="16-9,4-3")

    _file = await test_utils.download_zip_file(client, items_ids, "html_package", "wire")
    with ZipFile(_file) as zf:
        assert test_utils.get_download_filename("amazon-bookstore-opening.html", item) in zf.namelist()
        content = zf.open(test_utils.get_download_filename("amazon-bookstore-opening.html", item)).read()
    html_content_test(content)
    history = await test_utils.get_all("history")
    assert 4 == len(history)
    assert "download" in history[0]["action"]
    assert "download" in history[1]["action"]
    assert history[0].get("user")
    assert history[0].get("versioncreated") + timedelta(seconds=2) >= utcnow()
    assert history[0].get("item") in items_ids
    assert history[0].get("version")
    assert history[0].get("company") == bson.ObjectId("111111111111111111111111")
    assert history[0].get("section") == "wire"
