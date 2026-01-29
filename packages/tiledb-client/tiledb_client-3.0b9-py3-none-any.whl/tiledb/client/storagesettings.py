"""TileDB Storage Settings."""

from typing import Optional, Union

import tiledb

from . import client
from ._common.api_v4 import StorageSetting
from ._common.api_v4 import StoragesettingsApi
from ._common.api_v4 import StorageSettingsCreateRequest
from ._common.api_v4 import StorageSettingUpdateRequest
from .assets import TeamspaceLike
from .pager import Pager
from .rest_api import ApiException
from .teamspaces import _normalize_teamspace_id


class StorageSettingsError(tiledb.TileDBError):
    """Raised when storage settings can not be accessed."""


def create_storage_setting(
    *,
    name: str,
    is_default: bool,
    path: str,
    credentials_name: str,
    teamspace: Optional[TeamspaceLike] = None,
    _test_settings: Optional[bool] = True,
) -> StorageSetting:
    """Create a storage setting.

    Parameters
    ----------
    name : str
        A unique short name for the storage setting.
    is_default : bool
        Whether the storage setting is to be the default for its
        workspace or teamspace.
    path : str
        URI containing the VFS path of where assets will be stored.
        Local file paths must start with file://.
    credentials_name : str
        Name of the saved credential for access to `path`.
    teamspace : TeamspaceLike, optional
        The teamspace of the storage setting, specified by object or id.
        Omit this parameter to create a workspace storage setting.

    Returns
    -------
    StorageSetting

    Raises
    ------
    StorageSettingsError
        If the storage setting can not be created.

    Examples
    --------
    >>> setting = create_storage_setting(
    ...     name="storage_setting1",
    ...     is_default=True,
    ...     path="s3://bucket/prefix",
    ...     credentials_name="cred1",
    ...     teamspace="teamspace1",
    ... )
    >>> setting.name
    'storage_setting1'

    """
    # Teamspace id strictly required. To fix in Server?
    teamspace_id = _normalize_teamspace_id(teamspace)

    storage_settings_create_request = StorageSettingsCreateRequest(
        name=name,
        is_default=is_default,
        path=path,
        credentials_name=credentials_name,
        test_settings=_test_settings,
    )

    try:
        resp = client.build(StoragesettingsApi).create_storage_setting(
            client.get_workspace_id(),
            storage_settings_create_request,
            teamspace_id=teamspace_id,
        )
    except ApiException as exc:
        raise StorageSettingsError("Failed to create storage settings.") from exc
    else:
        return resp.data


def get_storage_setting(
    storage_setting: Union[str, object],
    *,
    teamspace: Optional[TeamspaceLike] = None,
) -> StorageSetting:
    """Get a credential by name.

    Parameters
    ----------
    storage_setting : str
        The storage setting identified by id or object.
    teamspace : TeamspaceLike, optional
        The teamspace of the storage setting. Omit this parameter to
        specify a workspace storage setting.

    Returns
    -------
    StorageSetting

    Raises
    ------
    StorageSettingsError
        If the storage setting can not be retrieved.

    Examples
    --------
    >>> storage_setting = get_storage_setting(
    ...     "storage_setting1",
    ...     teamspace="teamspace1"
    ... )
    >>> storage_setting.path
    's3://bucket/prefix'

    """
    setting_id = getattr(storage_setting, "storage_setting_id", storage_setting)

    # Teamspace id strictly required. To fix in Server?
    teamspace_id = _normalize_teamspace_id(teamspace)

    try:
        resp = client.build(StoragesettingsApi).get_storage_setting_by_id(
            setting_id,
            client.get_workspace_id(),
            teamspace_id=teamspace_id,
        )
    except ApiException as exc:
        raise StorageSettingsError("Failed to retrieve storage setting.") from exc
    else:
        return resp.data


def delete_storage_setting(
    storage_setting: Union[str, object],
    *,
    teamspace: Optional[TeamspaceLike] = None,
) -> None:
    """Delete a storage setting.

    Parameters
    ----------
    storage_setting : str
        The storage setting identified by id or object.
    teamspace : TeamspaceLike, optional
        The teamspace of the storage setting. Omit this parameter to
        specify a workspace storage setting.

    Raises
    ------
    StorageSettingsError
        If the storage setting can not be deleted.

    Examples
    --------
    >>> delete_storage_setting("storage_setting1", teamspace="teamspace1")

    """
    setting_id = getattr(storage_setting, "storage_setting_id", storage_setting)

    # Teamspace id strictly required. To fix in Server?
    teamspace_id = _normalize_teamspace_id(teamspace)

    try:
        client.build(StoragesettingsApi).delete_storage_setting_by_id(
            setting_id,
            client.get_workspace_id(),
            teamspace_id=teamspace_id,
        )
    except ApiException as exc:
        raise StorageSettingsError("Failed to delete storage setting.") from exc


def update_storage_setting(
    storage_setting: Union[str, object],
    *,
    name: Optional[str] = None,
    is_default: Optional[bool] = None,
    path: Optional[str] = None,
    credentials_name: Optional[str] = None,
    teamspace: Optional[TeamspaceLike] = None,
    _test_settings: Optional[bool] = True,
) -> None:
    """Update a storage setting.

    Parameters
    ----------
    storage_setting : str
        The storage setting identified by id or object.
    name : str, optional
        A unique short name for the storage setting.
    is_default : bool, optional
        Whether the storage setting is to be the default for its
        workspace or teamspace.
    path : str, optional
        URI containing the VFS path of where assets will be stored.
        Local file paths must start with file://.
    credentials_name : str, optional
        Name of the saved credential for access to `path`.
    teamspace : TeamspaceLike, optional
        The teamspace of the storage setting, specified by object or id.
        Omit this parameter to create a workspace storage setting.

    Raises
    ------
    StorageSettingsError
        If the credential can not be updated.

    Examples
    --------
    >>> update_storage_setting(
    ...     "storage_setting1",
    ...     credentials_name="cred2",
    ...     teamspace="teamspace1",
    ... )

    Updates the storage_setting1 of teamspace1 to use a new credential.

    """
    setting_id = getattr(storage_setting, "storage_setting_id", storage_setting)

    # Teamspace id strictly required. To fix in Server?
    teamspace_id = _normalize_teamspace_id(teamspace)

    storage_setting_update_request = StorageSettingUpdateRequest(
        name=name,
        is_default=is_default,
        path=path,
        credentials_name=credentials_name,
        test_settings=_test_settings,
    )

    try:
        client.build(StoragesettingsApi).patch_storage_setting_by_id(
            setting_id,
            client.get_workspace_id(),
            storage_setting_update_request,
            teamspace_id=teamspace_id,
        )
    except ApiException as exc:
        raise StorageSettingsError("Failed to update storage setting.") from exc


def list_storage_settings(
    teamspace: Optional[TeamspaceLike] = None,
    page: Optional[int] = 1,
    per_page: Optional[int] = None,
) -> Pager[StorageSetting]:
    """List storage settings.

    Parameters
    ----------
    teamspace : TeamspaceLike, optional
        The teamspace of the storage settings, specified by object or
        id. Omit this parameter to list workspace storage settings.
    page : int, optional
        Which page of results to retrieve. 1-based.
    per_page : int, optional
        How many results to include on each page.

    Returns
    -------
    Pager for StorageSettings

    Raises
    ------
    StorageSettingsError
        Raised when storage settings can not be listed.

    Examples
    --------

    """
    # Teamspace id strictly required. To fix in Server?
    teamspace_id = _normalize_teamspace_id(teamspace)

    try:
        resp = Pager(
            client.client.build(StoragesettingsApi).list_storage_settings,
            client.get_workspace_id(),
            teamspace_id=teamspace_id,
            per_page=per_page,
        )
        resp.call_page(page)
    except ApiException as exc:
        raise StorageSettingsError(
            "The storage setting listing request failed."
        ) from exc
    else:
        return resp
