from collections.abc import Mapping, Sequence
from typing import TypeAlias, final

from pydantic.dataclasses import dataclass
from typing_extensions import override

from .._constant import ScalarConstant
from .._identification import (
    ColumnIdentifier,
    HasIdentifier,
    HierarchyIdentifier,
    Identifiable,
    Identifier,
    LevelIdentifier,
    MeasureIdentifier,
    identify,
)
from .._measure_definition import MeasureDefinition
from .._py4j_client import Py4jClient
from .._py4j_client._utils import to_java_object, to_java_object_array
from .._pydantic import PYDANTIC_CONFIG as _PYDANTIC_CONFIG
from .utils import (
    create_hierarchy_identifier,
    create_level_identifier,
    create_store_field,
)

IdentifiersWithJavaEquivalent = ColumnIdentifier | HierarchyIdentifier | LevelIdentifier
PluginMeasureArgs: TypeAlias = (
    ScalarConstant | Identifiable[IdentifiersWithJavaEquivalent]
)

SequencePluginMeasureArgs: TypeAlias = (
    Sequence[PluginMeasureArgs]
    | PluginMeasureArgs
    | Mapping[str, PluginMeasureArgs]
    | Mapping[str, Sequence[PluginMeasureArgs]]
)

NestedPluginMeasureArgs: TypeAlias = (
    PluginMeasureArgs
    | SequencePluginMeasureArgs
    | Sequence[SequencePluginMeasureArgs]
    | Mapping[str, SequencePluginMeasureArgs]
)


def _extract_identifier(
    arg: Identifiable[IdentifiersWithJavaEquivalent], /, *, py4j_client: Py4jClient
) -> object:
    identifier = identify(arg)

    if not isinstance(
        identifier, IdentifiersWithJavaEquivalent
    ):  # pragma: no cover (missing tests)
        raise TypeError(f"Unsupported identifier type: {type(identifier)}")

    match identifier:
        case ColumnIdentifier():
            return create_store_field(identifier, py4j_client=py4j_client)
        case HierarchyIdentifier():
            return create_hierarchy_identifier(identifier, py4j_client=py4j_client)
        case LevelIdentifier():  # pragma: no branch (avoid `case _` to detect new variants)
            return create_level_identifier(identifier, py4j_client=py4j_client)


def _convert_plugin_measure_arg(
    arg: NestedPluginMeasureArgs,
    /,
    *,
    py4j_client: Py4jClient,
) -> object:
    if isinstance(arg, (Identifier, HasIdentifier)):
        return _extract_identifier(arg, py4j_client=py4j_client)
    if isinstance(arg, tuple):
        return to_java_object_array(
            [
                _convert_plugin_measure_arg(element, py4j_client=py4j_client)
                for element in arg
            ],
            gateway=py4j_client.gateway,
        )
    if isinstance(arg, list):
        return [
            _convert_plugin_measure_arg(element, py4j_client=py4j_client)
            for element in arg
        ]
    if isinstance(arg, Mapping):
        return {
            _convert_plugin_measure_arg(
                key,
                py4j_client=py4j_client,
            ): _convert_plugin_measure_arg(value, py4j_client=py4j_client)
            for key, value in arg.items()
        }

    # Nothing smarter to do. Transform the argument to a java array.
    return to_java_object(arg, gateway=py4j_client.gateway)


@final
@dataclass(config=_PYDANTIC_CONFIG, frozen=True, kw_only=True)
class PluginMeasure(MeasureDefinition):
    args: tuple[NestedPluginMeasureArgs, ...]
    plugin_key: str

    @override
    def _do_distil(
        self,
        identifier: MeasureIdentifier | None = None,
        /,
        *,
        cube_name: str,
        py4j_client: Py4jClient,
    ) -> MeasureIdentifier:
        return py4j_client.create_measure(
            identifier,
            self.plugin_key,
            *[
                _convert_plugin_measure_arg(
                    arg,
                    py4j_client=py4j_client,
                )
                for arg in self.args
            ],
            cube_name=cube_name,
        )
