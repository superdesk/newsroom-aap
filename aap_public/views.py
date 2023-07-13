import flask
from . import blueprint
from eve.utils import ParsedRequest
from superdesk import get_resource_service
import math


@blueprint.route('/widget-releases')
def widget_releases():
    return flask.render_template('aap-releases.html')


@blueprint.route('/aap-releases')
def aap_releases():
    return flask.render_template('aap-releases.html')


@blueprint.route('/releases', methods=['GET'])
def releases():
    referrer = flask.request.referrer.split('?')[0] if flask.request.referrer else "/"
    req = ParsedRequest()
    page = int(flask.request.args.get('from', 1))
    page_size = 10
    if flask.request.args.get('from'):
        req.page = page
    req.max_results = page_size
    service = get_resource_service('releases')
    list = service.get(req=req, lookup=None)

    items = dict()
    items['docs'] = list.docs
    for l in items['docs']:
        l['href'] = '{}?rkey={}'.format(referrer, l.get('_id'))

    items['total_pages'] = math.ceil(list.hits.get('hits').get('total') / page_size)
    items['page'] = page if page else 1
    items['last_page'] = referrer + '?from=' + str(items.get('total_pages'))
    if items.get('page') > 1:
        items['first_page'] = referrer
        items['prev_page'] = referrer + '?from=' + str(items.get('page') - 1)
    if page < items.get('total_pages'):
        items['next_page'] = referrer + '?from=' + str(items.get('page') + 1)

    content = flask.render_template('aapr_list.html', response=items)
    response = flask.Response(content)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@blueprint.route('/releases/<path:item_id>', methods=['GET'])
def get_release(item_id):
    service = get_resource_service('releases')
    req = ParsedRequest()
    item = service.find_one(req=req, _id=item_id)
    content = flask.render_template('aapr_item.html', item=item)
    response = flask.Response(content)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response
