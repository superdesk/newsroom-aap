import urllib
import json
import logging
from datetime import timedelta
from lxml import html as lxml_html
from lxml import etree
from urllib import parse
from PIL import Image
from copy import deepcopy

from superdesk.core import get_current_app
from superdesk.utc import utcnow
from superdesk.etree import to_string
from newsroom.utils import parse_date_str
from newsroom.media_utils import generate_renditions, store_image, get_watermark
from newsroom.assets import ASSETS_RESOURCE
from newsroom.wire.embeds import iterate_embeds
from PyRTF.document.paragraph import Paragraph
from PyRTF.Elements import LINE

AAP_PHOTOS_TOKEN = "AAP_PHOTOS_TOKEN"
logger = logging.getLogger(__name__)


def _fetch_photos(url):
    app = get_current_app().as_any()
    headers = {"Authorization": "Basic {}".format(app.config.get(AAP_PHOTOS_TOKEN))}
    request = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = response.read()
            json_data = json.loads(data.decode("utf-8"))
            return json_data
    except Exception:
        return {}


def get_media_cards_external(card):
    app = get_current_app().as_any()
    if (
        not app.config.get(AAP_PHOTOS_TOKEN)
        or not card.get("config")
        or not card.get("config").get("sources")
    ):
        return []

    cache_key = "home_photos_{}".format(card.get("_id"))
    if app.cache.get(cache_key):
        return app.cache.get(cache_key)

    cards = []
    assets = set()
    for item in card.get("config").get("sources"):
        if not item.get("url"):
            continue
        data = _fetch_photos(item.get("url"))
        count = int(item.get("count") or 1)
        if data.get("GalleryContainers"):
            containers = data.get("GalleryContainers")[:count]
            for container in containers:
                cards.append(
                    {
                        "media_url": container.get("CoverPictureLink"),
                        "description": container.get("Heading"),
                        "href": "{}/{}".format(
                            app.config.get("MULTIMEDIA_WEBSITE_URL"),
                            container.get("Link"),
                        ),
                    }
                )
        elif data.get("Assets"):
            asset_count = 0
            for asset in data.get("Assets"):
                asset_id = asset.get("AssetId")
                if asset_count >= count:
                    break
                parsed_url = parse.parse_qsl(item.get("url"))
                search = None
                query_string = []
                for url_item in parsed_url:
                    key, value = url_item
                    if "query" in key.lower():
                        search = parse.quote(value)
                    else:
                        query_string.append(url_item)

                href = app.config.get("MULTIMEDIA_WEBSITE_URL")
                if search:
                    href = "{}{}?{}".format(
                        app.config.get("MULTIMEDIA_WEBSITE_SEARCH_URL"),
                        search,
                        parse.urlencode(query_string),
                    )

                if asset_count < count and asset_id not in assets:
                    cards.append(
                        {
                            "media_url": asset.get("Layout", {}).get("Href"),
                            "description": asset.get("Title"),
                            "href": href,
                        }
                    )
                    assets.add(asset_id)
                    asset_count += 1

    app.cache.set(cache_key, cards, timeout=300)
    return cards


def set_photo_coverage_href(coverage, planning_item, deliveries=[]):
    app = get_current_app().as_any()
    plan_coverage = next(
        (
            c
            for c in (planning_item or {}).get("coverages") or []
            if c.get("coverage_id") == coverage.get("coverage_id")
        ),
        coverage,
    )
    content_type = plan_coverage.get("coverage_type") or (
        plan_coverage.get("planning") or {}
    ).get("g2_content_type")
    if (
        not plan_coverage
        or plan_coverage["workflow_status"] != "completed"
        or (
            content_type
            in [
                "picture",
                "video",
            ]
            and not app.config.get("MULTIMEDIA_WEBSITE_SEARCH_URL")
        )
        or (
            content_type == "video_explainer"
            and not app.config.get("EXPLAINERS_WEBSITE_URL")
        )
    ):
        return

    slugline = parse.quote(
        plan_coverage.get("slugline")
        or (
            plan_coverage.get("planning", {}).get(
                "slugline", (planning_item or {}).get("slugline")
            )
        )
    )
    scheduled = (
        parse_date_str(deliveries[0]["publish_time"])
        if len(deliveries) > 0 and (deliveries[0] or {}).get("publish_time")
        else utcnow()
    )
    from_date = scheduled - timedelta(hours=10)
    to_date = scheduled + timedelta(hours=2)

    video_keywords = (
        '{"Keyword":"NZN","Operator":"NOT"}, ' if content_type == "video" else ""
    )
    date_range_filter = (
        '"DateRange":[{"Start":"%s","End":"%s"}],"DateCreatedFilter":"false"'
        % (
            from_date.strftime("%Y-%m-%dT%H:%M:%S"),
            to_date.strftime("%Y-%m-%dT%H:%M:%S"),
        )
    )
    keyword_filter = '"SearchKeywords":[%s{"Keyword":"%s","Operator":"AND"}]' % (
        video_keywords,
        '\\"{}\\"'.format(slugline),
    )

    if content_type == "video":
        return '{}"{}"?q={{"MediaTypes":["video"],{}}}'.format(
            app.config.get("MULTIMEDIA_WEBSITE_SEARCH_URL"), slugline, date_range_filter
        )
    elif content_type == "video_explainer":
        return "{}?q={{{}, {}}}".format(
            app.config.get("EXPLAINERS_WEBSITE_URL"), keyword_filter, date_range_filter
        )
    elif content_type == "graphic":
        return '{}"{}"?q={{"supplementalcategory":"gra",{}}}'.format(
            app.config.get("MULTIMEDIA_WEBSITE_SEARCH_URL"),
            slugline,
            date_range_filter,
        )
    else:
        return '{}"{}"?q={{"MediaTypes":["image"],{}}}'.format(
            app.config.get("MULTIMEDIA_WEBSITE_SEARCH_URL"), slugline, date_range_filter
        )


def generate_embed_renditions(item):
    app = get_current_app().as_any()

    def _get_source_ref(marker, item):
        try:
            return (
                item.get("associations")
                .get(marker)
                .get("renditions")
                .get("_newsroom_custom")
                .get("href")
            )
        except (AttributeError, TypeError):
            return None

    has_editor_assoc = False
    # generate required watermarked renditions for any embedded renditions
    for name, association in ((item.get("associations") or {})).items():
        if name.startswith("editor_") and association:
            generate_preview_details_renditions(
                item.get("associations", {}).get(name), "viewImage"
            )
            has_editor_assoc = True

    if has_editor_assoc:
        html_updated = False
        root_elem = lxml_html.fromstring(item.get("body_html", ""))
        for comment, editor_id in iterate_embeds(root_elem):
            figure_elem = comment.xpath("following-sibling::figure[1]")
            if figure_elem:
                figure_elem = figure_elem[0]
                if figure_elem is not None and figure_elem.tag == "figure":
                    elem = figure_elem.find("./img")
                    if elem is not None:
                        elem.attrib["id"] = editor_id
                        src = _get_source_ref(editor_id, item)
                        if src:
                            elem.attrib["src"] = src
                            html_updated = True

            embed_item = (item.get("associations") or {}).get(editor_id) or {}
            byline = embed_item.get("byline")
            guid = embed_item.get("guid", None)

            embed_link_url = (
                embed_item.get("guid")
                if isinstance(guid, str) and len(guid) == 20 and guid.isdigit()
                else None
            )
            if embed_link_url:
                embed_link_url = (
                    app.config.get("MULTIMEDIA_WEBSITE_SEARCH_URL") + embed_link_url
                )
            caption_results = comment.xpath(
                "./following-sibling::figure[1]//figcaption"
            )
            if caption_results:
                caption_elem = caption_results[0]
                current_text = (caption_elem.text or "").strip()
                caption_elem.text = f"{current_text} (" if current_text else "("
                if embed_link_url:
                    a_tag = etree.SubElement(caption_elem, "a")
                    a_tag.set("href", embed_link_url)
                    a_tag.text = byline
                    a_tag.tail = ")"
                else:
                    caption_elem.text += f"{byline})"
                html_updated = True

        if html_updated:
            item["body_html"] = to_string(root_elem, method="html")

        # If there is no feature media them copy the last embedded image to be the feature media
        if not ((item.get("associations") or {}).get("featuremedia") or {}).get(
            "renditions"
        ):
            item["associations"]["featuremedia"] = deepcopy(
                item.get("associations").get(editor_id)
            )
            generate_renditions(item)

    extra = item.get("extra") or {}

    # Prepend verdict if present
    if "claim_verdict" in extra:
        verdict_html = f"<p><b>OUR VERDICT</b></p>{extra.get('claim_verdict', '')}"
        item["body_html"] = verdict_html + (item.get("body_html") or "")

    # Prepend short text if present
    if "claim_short_text" in extra:
        claim_html = (
            f"<p><b>WHAT WAS CLAIMED</b></p>{extra.get('claim_short_text', '')}"
        )
        item["body_html"] = claim_html + (item.get("body_html") or "")


def generate_preview_details_renditions(picture, src_rendition="16-9"):
    app = get_current_app().as_any()
    """Generate preview and details rendition"""
    if (
        not picture
        or not picture.get("renditions")
        or not picture.get("renditions").get("16-9")
    ):
        logger.warning("Invalid renditions. picture: {}".format(picture))
        return

    # add watermark to base/view images
    rendition = picture.get("renditions", {}).get(src_rendition)
    if rendition:
        binary = app.media.get(rendition["media"], resource=ASSETS_RESOURCE)
        im = Image.open(binary)
        watermark = get_watermark(im)
        custom = store_image(
            watermark, _id="%s%s" % (rendition["media"], "_newsroom_custom")
        )
        picture["renditions"].update(
            {
                "_newsroom_custom": custom,
            }
        )


def customize_rtf_file(rtf_document):
    section = rtf_document.Sections[0]
    ss = rtf_document.StyleSheet
    p1 = Paragraph(ss.ParagraphStyles.Normal)
    footer = """COPYRIGHT & DISCLAIMER: This report and its contents are for the use "
    "of AAPNewswire subscribers only and may not be provided to any third party for "
    "any purpose whatsoever without the express written permission of Australian "
    "Associated Press Pty Ltd. The material contained in this report is for general "
    "information purposes only. Any figures in this report are an estimation and should "
    "not be taken as definitive statistics. Subscribers should refer to the original "
    "article before making any financial decisions or forming any opinions. AAP "
    "Newswire Monitoring makes no representations and, to the extent permitted "
    "by law, excludes all warranties in relation to the information contained "
    "in the report and is not liable to you or to any third party for any "
    "losses, costs or expenses, resulting from any use or misuse of the report."""
    p1.append(
        LINE,
        footer,
        LINE,
        "AAPNewswire report supplied by",
        LINE,
        "Copyright AAPNewswire {}".format(utcnow().strftime("%Y")),
    )
    section.append(p1)
    return


def init_app(app):
    app.set_photo_coverage_href = set_photo_coverage_href
    app.get_media_cards_external = get_media_cards_external
    app.generate_preview_details_renditions = generate_preview_details_renditions
    app.generate_embed_renditions = generate_embed_renditions
    app.customize_rtf_file = customize_rtf_file
