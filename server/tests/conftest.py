from pathlib import Path

from newsroom.tests.conftest import (  # noqa
    event_loop_policy,
    app,
    client,
    use_config_file,
)

use_config_file(str(Path(__file__).parent.parent.joinpath("settings.py").resolve()))
