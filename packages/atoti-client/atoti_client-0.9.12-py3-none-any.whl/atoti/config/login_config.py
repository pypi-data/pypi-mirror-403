from __future__ import annotations

from collections.abc import Set as AbstractSet
from typing import Annotated, final

from pydantic import Field
from pydantic.dataclasses import dataclass

from .._pydantic import PYDANTIC_CONFIG as _PYDANTIC_CONFIG


@final
@dataclass(config=_PYDANTIC_CONFIG, frozen=True, kw_only=True)
class LoginConfig:
    """The config related to the ``/login`` endpoint."""

    allowed_redirect_urls: Annotated[AbstractSet[str], Field(min_length=1)] | None = (
        None
    )

    """The allowed values of the ``redirectUrl`` query parameter.

    If ``None``, all URLs are allowed.
    """
