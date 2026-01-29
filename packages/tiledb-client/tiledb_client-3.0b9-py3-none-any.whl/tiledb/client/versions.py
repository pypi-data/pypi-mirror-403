"""Retrieve TileDB Server version information."""

import tiledb

from ._common.api_v4.api import VersionsApi
from ._common.api_v4.models import Versions
from .client import client
from .rest_api import ApiException


class VersionsError(tiledb.TileDBError):
    """Raised when server versions can not be accessed."""


def get_versions() -> Versions:
    """Get server versions information.

    Includes Go version, TileDB version, and versions of UDF images.

    Returns
    -------
    Versions

    Raises
    ------
    VersionsError:
        When server versions can not be retrieved.

    """
    try:
        versions_response = client.build(VersionsApi).get_versions()
    except ApiException as exc:
        raise VersionsError("The server versions retrieval failed.") from exc
    else:
        return versions_response.data
