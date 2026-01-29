from collections.abc import Callable
from importlib import import_module

from ._pydantic import get_type_adapter
from ._resources_directory import RESOURCES_DIRECTORY

_API_JSON_SNAPSHOT_PATH = RESOURCES_DIRECTORY / "api.json"

_ApiSnapshot = dict[str, dict[str, list[str]]]


def decorate_api(
    decorator: Callable[[Callable[..., object]], Callable[..., object]], /
) -> None:
    api_snapshot_bytes = _API_JSON_SNAPSHOT_PATH.read_bytes()
    api_snapshot = get_type_adapter(_ApiSnapshot).validate_json(api_snapshot_bytes)

    for module_name, attribute_names_from_class_name in api_snapshot.items():
        module: object

        try:
            module = import_module(module_name)
        except ModuleNotFoundError:  # pragma: no cover
            # Can happen when trying to decorate the API of a plugin that is not installed.
            continue

        for (
            class_name,
            attribute_names,
        ) in attribute_names_from_class_name.items():
            container = getattr(module, class_name) if class_name else module
            for attribute_name in attribute_names:
                attribute = getattr(container, attribute_name)
                try:
                    if callable(attribute):
                        attribute = decorator(attribute)
                    else:
                        assert isinstance(attribute, property)
                        # spell-checker: disable-next-line
                        fdel = decorator(attribute.fdel) if attribute.fdel else None
                        fget = decorator(attribute.fget) if attribute.fget else None
                        fset = decorator(attribute.fset) if attribute.fset else None
                        if (
                            # spell-checker: disable-next-line
                            fdel is not attribute.fdel
                            or fget is not attribute.fget
                            or fset is not attribute.fset
                        ):
                            attribute = property(
                                doc=attribute.__doc__,
                                # spell-checker: disable-next-line
                                fdel=fdel,  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]
                                fget=fget,
                                fset=fset,  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]
                            )
                except Exception as error:  # pragma: no cover
                    # Not relying only on `raise ... from error` because this error is raised to early in pytest's initialization to display the details of the original `error`.
                    raise RuntimeError(
                        f"Failed to decorate {attribute}(). {error}"
                    ) from error
                else:
                    setattr(container, attribute_name, attribute)
