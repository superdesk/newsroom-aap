
import os
from newsroom.default_settings import BLUEPRINTS as blueprints

if os.environ.get('PUSH'):
    BLUEPRINTS = blueprints
else:
    BLUEPRINTS = [blueprint for blueprint in blueprints if 'push' not in blueprint]
