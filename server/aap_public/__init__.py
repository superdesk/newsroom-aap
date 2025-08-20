from quart import Blueprint

blueprint = Blueprint("aap_public", __name__)

from . import views  # noqa
