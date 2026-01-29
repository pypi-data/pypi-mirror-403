"""TileDB Credentials."""

from typing import Optional

import tiledb

from . import client
from ._common.api_v4 import AccessCredential  # noqa: F401
from ._common.api_v4 import AccessCredentialRole  # noqa: F401
from ._common.api_v4 import AWSCredential  # noqa: F401
from ._common.api_v4 import AWSRole  # noqa: F401
from ._common.api_v4 import AzureCredential  # noqa: F401
from ._common.api_v4 import AzureToken  # noqa: F401
from ._common.api_v4 import CloudProvider
from ._common.api_v4 import Credential  # noqa: F401
from ._common.api_v4 import CredentialCreateRequest
from ._common.api_v4 import CredentialsApi
from ._common.api_v4 import CredentialsVerifyRequest
from ._common.api_v4 import CredentialUpdateRequest
from ._common.api_v4 import GCPInteroperabilityCredential  # noqa: F401
from ._common.api_v4 import GCPServiceAccountKey  # noqa: F401
from ._common.api_v4 import Token  # noqa: F401
from .assets import TeamspaceLike
from .pager import Pager
from .rest_api import ApiException
from .teamspaces import _normalize_teamspace_id


class CredentialsError(tiledb.TileDBError):
    """Raised when credentials can not be accessed."""


def create_credential(
    name: str,
    provider: CloudProvider,
    *,
    teamspace: Optional[TeamspaceLike] = None,
    provider_default: Optional[bool] = None,
    allowed_in_tasks: Optional[bool] = None,
    credential: Optional[Credential] = None,
    role: Optional[AccessCredentialRole] = None,
    token: Optional[Token] = None,
) -> None:
    """Create a credential stored by name.

    Note that `credential`, `role`, and `token` are mutually exclusive,
    and that credential parameters are not verified during creation.

    Parameters
    ----------
    name : str
        A unique short name for the credential.
    provider : CloudProvider
        Cloud provider short name.
    teamspace : TeamspaceLike, optional
        The teamspace to which the credential will be saved, specified
        by object or id. Omit this parameter to create a workspace
        credential.
    provider_default : bool, optional
        Whether the credential is to be the default for its cloud
        provider. Default: False.
    allowed_in_tasks : bool, optional
        Whether the credential is allowed to be used in tasks. Default:
        False.
    credential : Credential, optional
        A credential object using keys.
    role : AccessCredentialRole, optional
        A credential object using a provider role.
    token : Token, optional
        A credential object using a provider token.

    Raises
    ------
    CredentialsError
        If the credential can not be created.

    Examples
    --------
    >>> create_credential(
    ...     "cred1",
    ...     "AWS",
    ...     teamspace="teamspace1",
    ...     role=AccessCredentialRole(
    ...         aws=AWSRole(
    ...             role_arn="arn:aws:iam::123456789012:role/demo",
    ...             external_id="123ABC"
    ...         )
    ...     )
    ... )

    """
    # Teamspace id strictly required. To fix in Server?
    teamspace_id = _normalize_teamspace_id(teamspace)

    credential_create_request = CredentialCreateRequest(
        name=name,
        provider_default=provider_default,
        provider=provider,
        allowed_in_tasks=False,
        credential=credential,
        role=role,
        token=token,
    )

    try:
        client.build(CredentialsApi).create_credential(
            client.get_workspace_id(),
            credential_create_request,
            teamspace_id=teamspace_id,
        )
    except ApiException as exc:
        raise CredentialsError("Failed to create credential.") from exc


def get_credential(
    name: str,
    *,
    teamspace: Optional[TeamspaceLike] = None,
) -> AccessCredential:
    """Get a credential by name.

    Parameters
    ----------
    name : str
        Name of the credential.
    teamspace : TeamspaceLike, optional
        The teamspace of the credential. Omit this parameter to specify
        a workspace credential.

    Returns
    -------
    AccessCredential

    Raises
    ------
    CredentialsError
        If the credential can not be retrieved.

    Examples
    --------
    >>> cred = get_credential("cred1", teamspace="teamspace1")
    >>> cred.role.aws.role_arn
    'arn:aws:iam::123456789012:role/demo'

    """
    # Teamspace id strictly required. To fix in Server?
    teamspace_id = _normalize_teamspace_id(teamspace)

    try:
        resp = client.build(CredentialsApi).get_credential_by_name(
            client.get_workspace_id(),
            name,
            teamspace_id=teamspace_id,
        )
    except ApiException as exc:
        raise CredentialsError("Failed to retrieve credential.") from exc
    else:
        return resp.data


def delete_credential(
    name: str,
    *,
    teamspace: Optional[TeamspaceLike] = None,
) -> None:
    """Delete a credential by name.

    Parameters
    ----------
    name : str
        Name of the credential.
    teamspace : TeamspaceLike, optional
        The teamspace of the credential. Omit this parameter to specify
        a workspace credential.

    Raises
    ------
    CredentialsError
        If the credential can not be deleted.

    """
    # Teamspace id strictly required. To fix in Server?
    teamspace_id = _normalize_teamspace_id(teamspace)

    try:
        client.build(CredentialsApi).delete_credential_by_name(
            client.get_workspace_id(),
            name,
            teamspace_id=teamspace_id,
        )
    except ApiException as exc:
        raise CredentialsError("Failed to delete credential.") from exc


def update_credential(
    cred_name: str,
    *,
    teamspace: Optional[TeamspaceLike] = None,
    name: Optional[str] = None,
    provider_default: Optional[bool] = None,
    provider: Optional[CloudProvider] = None,
    allowed_in_tasks: Optional[bool] = None,
    credential: Optional[Credential] = None,
    role: Optional[AccessCredentialRole] = None,
    token: Optional[Token] = None,
) -> None:
    """Update a credential by name.

    Renaming or otherwise modifying a credential may impact programs
    that rely upon it.

    Note that `credential`, `role`, and `token` are mutually exclusive.

    Parameters
    ----------
    cred_name : str
        Name of the credential.
    teamspace : TeamspaceLike, optional
        The teamspace in which the credential is registered, specified
        by object or id. Omit this parameter to choose a workspace
        credential.
    name : str, optional
        New name for the credential.
    provider_default : bool, optional
        Toggle whether the credential is to be the default for its
        cloud provider.
    provider : CloudProvider, optional
        Change the cloud provider name.
    allowed_in_tasks : bool, optional
        Toggle whether the credential is allowed to be used in tasks.
    credential : Credential, optional
        Change the credential's keys.
    role : AccessCredentialRole, optional
        Change the role of the credential.
    token : Token, optional
        Change the credential's token.

    Raises
    ------
    CredentialsError
        If the credential can not be updated.

    Examples
    --------
    >>> update_credential(
    ...     "cred1",
    ...     teamspace="teamspace1",
    ...     credential=Credential(
    ...         AWSCredential(
    ...             access_key_id="AWS_ACCESS_KEY_ID",
    ...             secret_access_key="AWS_SECRET_ACCESS_KEY",
    ...         )
    ...     )
    ... )

    Updates the keys of the AWS credential named "cred1" in teamspace1.

    """
    # Teamspace id strictly required. To fix in Server?
    teamspace_id = _normalize_teamspace_id(teamspace)

    credential_update_request = CredentialUpdateRequest(
        name=name,
        provider_default=provider_default,
        provider=provider,
        allowed_in_tasks=False,
        credential=credential,
        role=role,
        token=token,
    )

    try:
        client.build(CredentialsApi).patch_credential_by_name(
            client.get_workspace_id(),
            cred_name,
            credential_update_request,
            teamspace_id=teamspace_id,
        )
    except ApiException as exc:
        raise CredentialsError("Failed to update credential.") from exc


def list_credentials(
    teamspace: Optional[TeamspaceLike] = None,
    page: Optional[int] = 1,
    per_page: Optional[int] = None,
) -> Pager[AccessCredential]:
    """List credentials.

    Parameters
    ----------
    teamspace : TeamspaceLike, optional
        The teamspace of the storage settings, specified
        by object or id. Omit this parameter to list workspace
        storage settings.
    page : int, optional
        Which page of results to retrieve. 1-based.
    per_page : int, optional
        How many results to include on each page.

    Returns
    -------
    Pager for AccessCredentials

    Raises
    ------
    CredentialsError
        Raised when access credentials can not be listed.

    Examples
    --------
    >>> for cred in list_credentials(teamspace="teamspace1"):
    ...     print(cred.name)
    ...
    cred1

    """
    # Teamspace id strictly required. To fix in Server?
    teamspace_id = _normalize_teamspace_id(teamspace)

    try:
        resp = Pager(
            client.client.build(CredentialsApi).get_credentials,
            client.get_workspace_id(),
            teamspace_id=teamspace_id,
            per_page=per_page,
        )
        resp.call_page(page)
    except ApiException as exc:
        raise CredentialsError(
            "The access credentials listing request failed."
        ) from exc
    else:
        return resp


def verify_credential(
    name: str,
    provider: CloudProvider,
    *,
    teamspace: Optional[TeamspaceLike] = None,
    provider_default: Optional[bool] = None,
    allowed_in_tasks: Optional[bool] = None,
    credential: Optional[Credential] = None,
    role: Optional[AccessCredentialRole] = None,
    token: Optional[Token] = None,
) -> None:
    """Verify a credential stored by name.


    Verification of credentials is mostly structural; existence and
    consistency of object attributes are checked. In the case of
    credentials based on AWS roles (see the `role` parameter below),
    stricter verification is performed.

    Parameters
    ----------
    name : str
        A unique short name for the credential.
    provider : CloudProvider
        Cloud provider short name.
    teamspace : TeamspaceLike, optional
        The teamspace of the credential, specified by object or id. Omit
        this parameter to specify a workspace credential.
    provider_default : bool, optional
        Whether the credential is to be the default for its
        cloud provider. Default: False.
    allowed_in_tasks : bool, optional
        Whether the credential is allowed to be used in tasks. Default:
        False.
    credential : Credential, optional
        A credential object using keys.
    role : AccessCredentialRole, optional
        A credential object using a provider role.
    token : Token, optional
        A credential object using a provider token.

    Raises
    ------
    CredentialsError
        If the credential parameters do not meet server requirements.

    Examples
    --------
    >>> verify_credential(
    ...     "cred1",
    ...     "AWS",
    ...     teamspace="teamspace1",
    ...     role=AccessCredentialRole(
    ...         aws=AWSRole(
    ...             role_arn="arn:aws:iam::123456789012:role/demo",
    ...             external_id="123ABC"
    ...         )
    ...     )
    ... )

    """
    # Teamspace id strictly required. To fix in Server?
    teamspace_id = _normalize_teamspace_id(teamspace)

    credentials_verify_request = CredentialsVerifyRequest(
        name=name,
        provider_default=provider_default,
        provider=provider,
        allowed_in_tasks=allowed_in_tasks,
        credential=credential,
        role=role,
        token=token,
        workspace_id=client.get_workspace_id(),
        teamspace_id=teamspace_id,
    )

    try:
        client.build(CredentialsApi).verify_credential(
            credentials_verify_request,
        )
    except ApiException as exc:
        raise CredentialsError("Failed to verify credential.") from exc
