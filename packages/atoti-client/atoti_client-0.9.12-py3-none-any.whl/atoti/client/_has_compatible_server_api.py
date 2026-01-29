from .._atoti_server_version import atoti_server_version
from ._server_versions import ServerVersions


def has_compatible_server_api(server_versions: ServerVersions, /) -> bool:
    if "atoti" not in server_versions.apis:  # pragma: no cover (missing tests)
        return False

    expected_server_version = atoti_server_version()

    return (
        server_versions.server_version == expected_server_version
        or server_versions.server_version.endswith(  # To support development on local builds of Atoti Server.
            "-SNAPSHOT"
        )
    )
