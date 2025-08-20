from newsroom.formatters import register_formatter
from .ninjs3 import NINJSFormatter3
from .html import HTMLFormatter
from .downloadninjs import NINJSDownloadFormatter
from .htmlpackage import HTMLPackageFormatter
from .htmlwithmedia import HTMLMediaFormatter


def init_app(app):
    register_formatter(NINJSFormatter3)
    register_formatter(HTMLFormatter)
    register_formatter(NINJSDownloadFormatter)
    register_formatter(HTMLPackageFormatter)
    register_formatter(HTMLMediaFormatter)
