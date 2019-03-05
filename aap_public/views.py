import flask
from . import blueprint


@blueprint.route('/widget-releases')
def widget_releases():
    return flask.render_template('widget-releases.html')
