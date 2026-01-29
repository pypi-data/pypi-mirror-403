from warnings import warn as _warn

from . import (
    agg as agg,
    array as array,
    finance as finance,
    function as function,
    math as math,
    stats as stats,
    string as string,
)
from ._auto_cap_http_requests import (
    auto_cap_http_requests as _auto_cap_http_requests,
)
from ._compose_decorators import compose_decorators as _compose_decorators
from ._data_type import DataType as DataType
from ._decorate_api import decorate_api as _decorate_api
from ._deprecated_warning_category import (
    DEPRECATED_WARNING_CATEGORY as _DEPRECATED_WARNING_CATEGORY,
)
from ._eula import (
    EULA as __license__,  # noqa: N811, F401
    hide_new_eula_message as hide_new_eula_message,
    print_eula_message as _print_eula_message,
)
from ._py4j_client._utils import patch_databricks_py4j as _patch_databricks_py4j
from ._telemetry import telemeter as _telemeter
from ._validate_call import validate_call as _validate_call
from .aggregate_cache import AggregateCache as AggregateCache
from .aggregate_provider import *
from .app_extension import ADVANCED_APP_EXTENSION as ADVANCED_APP_EXTENSION
from .authentication import *
from .client import *
from .client_side_encryption_config import (
    ClientSideEncryptionConfig as ClientSideEncryptionConfig,
)
from .cluster_definition import ClusterDefinition as ClusterDefinition
from .column import Column as Column
from .config import *
from .cube import Cube as Cube
from .data_load import CsvLoad as CsvLoad
from .directquery import *
from .distribution import *
from .distribution_protocols import *
from .experimental import experimental as experimental
from .function import *
from .hierarchy import Hierarchy as Hierarchy
from .key_pair import KeyPair as KeyPair
from .level import Level as Level
from .mapping_lookup import mapping_lookup as mapping_lookup
from .mdx_query_result import MdxQueryResult as MdxQueryResult
from .measure import Measure as Measure
from .order import *
from .scope import *
from .session import Session as Session
from .table import Table as Table
from .type import *
from .user import User as User

_print_eula_message()

_patch_databricks_py4j()

_telemeter()

_decorate_api(
    _compose_decorators(
        _auto_cap_http_requests,
        _validate_call,
    )
)


def __getattr__(name: str) -> object:
    match name:
        case "ParquetLoad":
            _warn(
                f"Importing `{name}` from `atoti` is deprecated, import it from `atoti_parquet` instead.",
                category=_DEPRECATED_WARNING_CATEGORY,
                stacklevel=2,
            )

            from atoti_parquet import (  # pylint: disable=nested-import,undeclared-dependency
                ParquetLoad,
            )

            return ParquetLoad
        case _:
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
