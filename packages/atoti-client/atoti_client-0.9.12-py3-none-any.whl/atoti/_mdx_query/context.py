from collections.abc import Mapping
from typing import TypeAlias

from .._context_value import ContextValue

Context: TypeAlias = Mapping[str, ContextValue]
