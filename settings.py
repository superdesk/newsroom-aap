
import os
from newsroom.default_settings import BLUEPRINTS as blueprints, CORE_APPS

if os.environ.get('PUSH'):
    BLUEPRINTS = blueprints
else:
    BLUEPRINTS = [blueprint for blueprint in blueprints if 'push' not in blueprint]

CORE_APPS.append('instrumentation')
