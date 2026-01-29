from __future__ import annotations

from .._doc import doc
from .._experimental import experimental
from .._measure.plugin_measure import NestedPluginMeasureArgs, PluginMeasure
from .._measure_definition import MeasureDefinition


@doc()
@experimental("plugin_measure")
def plugin_measure(
    *args: NestedPluginMeasureArgs, plugin_key: str
) -> MeasureDefinition:
    """Return a measure computed by a plugin registered by an :atoti_server_docs:`Atoti Server extension <starters/how-to/create-custom-measures>`.

    Warning:
        {experimental_feature}

    Args:
        args: The arguments forwarded to the measure plugin.
            Supported types include:

            * Scalar (any non-array :mod:`data type <atoti.type>`)
            * :class:`~atoti.Column`
            * :class:`~atoti.Hierarchy`
            * :class:`~atoti.Level`
            * Any :class:`dict`, :class:`list` or :class:`tuple` of the above types.

        plugin_key: The key of the measure plugin.

    Example:
        .. doctest::
            :hide:

            >>> from .._resources_directory import RESOURCES_DIRECTORY
            >>> server_extension_jar_path = TEST_RESOURCES_PATH / "server-extension.jar"

        >>> session_config = tt.SessionConfig(extra_jars=[server_extension_jar_path])
        >>> session = tt.Session.start(session_config)
        >>> df = pd.DataFrame(
        ...     [("Phone", 2), ("Watch", 4), ("Laptop", 1)],
        ...     columns=["Product", "Quantity"],
        ... )
        >>> table = session.read_pandas(
        ...     df,
        ...     keys={{"Product"}},
        ...     table_name="Example",
        ... )
        >>> cube = session.create_cube(table)
        >>> l, m = cube.levels, cube.measures

        The Atoti Server extension used provided by ``server_extension_jar_path`` contributes a measure plugin with the key ``"MY_INCREMENT"``:

        >>> with tt.experimental({{"plugin_measure"}}):
        ...     m["Incremented quantity.SUM"] = tt.plugin_measure(
        ...         m["Quantity.SUM"].name, l["Product"], 2, plugin_key="MY_INCREMENT"
        ...     )
        >>> cube.query(
        ...     m["Quantity.SUM"],
        ...     m["Incremented quantity.SUM"],
        ...     levels=[l["Product"]],
        ... )
                Quantity.SUM Incremented quantity.SUM
        Product
        Laptop             1                        3
        Phone              2                        4
        Watch              4                        6

    """
    return PluginMeasure(args=args, plugin_key=plugin_key)
