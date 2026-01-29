from math import ceil
from warnings import warn

from .._deprecated_warning_category import DEPRECATED_WARNING_CATEGORY
from .._typing import Duration
from .context import Context


def handle_deprecated_timeout(
    context: Context, /, *, timeout: Duration | None
) -> Context:
    if timeout is not None:  # pragma: no cover (deprecated)
        warn(
            "The `timeout` parameter is deprecated. Pass a ``queriesTimeLimit`` in the ``context`` argument instead.",
            category=DEPRECATED_WARNING_CATEGORY,
            stacklevel=3,
        )
        return {
            "queriesTimeLimit": ceil(timeout.total_seconds()),
            **context,
        }

    return context
