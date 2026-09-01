from quart_babel import lazy_gettext
from newsroom.wire.formatters import NINJSWithoutEmbedsFormatter


class NINJSFormatter3(NINJSWithoutEmbedsFormatter):
    """
    Wrapper class for backward compatibility
    """

    format_id = "ninjs_formatter_three"
    name = lazy_gettext("Ninjs with no embeds backward compatible")
