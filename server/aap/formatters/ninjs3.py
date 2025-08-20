from quart_babel import lazy_gettext
from newsroom.utils import remove_all_embeds
from newsroom.wire.formatters import NINJSFormatter2


class NINJSFormatter3(NINJSFormatter2):
    """
    Format with no Embeds, some API subscribers are unable to handle them!
    """

    format_id = "ninjs3"
    name = lazy_gettext("Ninjs with no embeds")

    async def _transform_to_ninjs(self, item):
        remove_all_embeds(item)
        ninjs = await super()._transform_to_ninjs(item)
        return ninjs
