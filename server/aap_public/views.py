import quart
from . import blueprint
from eve.utils import ParsedRequest
from superdesk import get_resource_service
import math


@blueprint.route("/widget-releases")
async def widget_releases():
    return await quart.render_template("aap-releases.html")


@blueprint.route("/aap-releases")
async def aap_releases():
    return await quart.render_template("aap-releases.html")


@blueprint.route("/releases", methods=["GET"])
async def releases():
    referrer = quart.request.referrer.split("?")[0] if quart.request.referrer else "/"
    req = ParsedRequest()
    page = int(quart.request.args.get("from", 1))
    page_size = 10
    if quart.request.args.get("from"):
        req.page = page
    req.max_results = page_size
    service = get_resource_service("releases")
    list = service.get(req=req, lookup=None)

    items = dict()
    items["docs"] = list.docs
    for _l in items["docs"]:
        _l["href"] = "{}?rkey={}".format(referrer, _l.get("_id"))

    items["total_pages"] = math.ceil(
        list.hits.get("hits").get("total", {}).get("value", 0) / page_size
    )
    items["page"] = page if page else 1
    items["last_page"] = referrer + "?from=" + str(items.get("total_pages"))
    if items.get("page") > 1:
        items["first_page"] = referrer
        items["prev_page"] = referrer + "?from=" + str(items.get("page") - 1)
    if page < items.get("total_pages"):
        items["next_page"] = referrer + "?from=" + str(items.get("page") + 1)

    content = await quart.render_template("aapr_list.html", response=items)
    response = quart.Response(content)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@blueprint.route("/releases/<path:item_id>", methods=["GET"])
async def get_release(item_id):
    service = get_resource_service("releases")
    req = ParsedRequest()
    item = service.find_one(req=req, _id=item_id)
    content = await quart.render_template("aapr_item.html", item=item)
    response = quart.Response(content)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response
