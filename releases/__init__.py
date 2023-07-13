import superdesk
from .resource import AAPReleaseResource
from newsroom import Service


def init_app(app):
    superdesk.register_resource('releases', AAPReleaseResource, Service, _app=app)
