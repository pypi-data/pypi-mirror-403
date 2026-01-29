from __future__ import annotations

import os

from _atoti_core import LICENSE_KEY_ENV_VAR_NAME

from .._env import get_env_flag
from .import_event import ImportEvent
from .send_event import send_event

_DISABLE_TELEMETRY_ENV_VAR_NAME = "_ATOTI_DISABLE_TELEMETRY"


def telemeter() -> None:
    if LICENSE_KEY_ENV_VAR_NAME in os.environ or get_env_flag(
        _DISABLE_TELEMETRY_ENV_VAR_NAME,
    ):
        return

    send_event(ImportEvent())
