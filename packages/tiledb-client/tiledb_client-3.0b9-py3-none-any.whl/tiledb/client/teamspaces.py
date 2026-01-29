"""TileDB Teamspaces

A teamspace is a container for assets and folders of assets. It will be
backed by a unique cloud storage location and may be mounted as a
directory in Notebooks and UDFs.

The TileDB web UI is the primary tool for managing teamspaces, but some
functionality is available via this module.
"""

from dataclasses import dataclass
from typing import List, Optional, Sequence, Union

import tiledb
from tiledb.client import client
from tiledb.client._common.api_v4.api import TeamspacesApi
from tiledb.client._common.api_v4.exceptions import ApiException
from tiledb.client._common.api_v4.models import Teamspace
from tiledb.client._common.api_v4.models import TeamspaceRole
from tiledb.client._common.api_v4.models import TeamspacesCreateRequest
from tiledb.client._common.api_v4.models import TeamspaceUser
from tiledb.client._common.api_v4.models import TeamspaceUsersBulkUpdateRequestInner
from tiledb.client._common.api_v4.models import TeamspaceUsersCreateRequestInner
from tiledb.client._common.api_v4.models import TeamspaceVisibility
from tiledb.client._common.api_v4.models import User

from .pager import Pager

# Re-export the models for convenience.
__all__ = [
    "Member",
    "Teamspace",
    "TeamspaceRole",
    "TeamspaceUser",
    "User",
    "TeamspaceVisibility",
    "TeamspacesError",
    "create_teamspace",
    "list_teamspaces",
    "delete_teamspace",
    "get_teamspace",
    "list_teamspace_members",
    "add_teamspace_members",
    "update_teamspace_member_roles",
    "remove_teamspace_members",
]


@dataclass
class Member:
    """Like TeamspaceUser, but minimally satisfying member addition needs."""

    user_id: Union[str, User]
    role: TeamspaceRole = TeamspaceRole.VIEWER


class TeamspacesError(tiledb.TileDBError):
    """Raised when a teamspaces CRUD operation fails."""


def _normalize_teamspace_id(teamspace: Union[str, Teamspace]) -> str:
    """Normalize teamspace arguments to an id."""
    if isinstance(teamspace, Teamspace):
        return teamspace.teamspace_id
    elif isinstance(teamspace, str):
        if teamspace.startswith("ts_"):
            return teamspace
        else:
            try:
                teamspace_id = get_teamspace(teamspace).teamspace_id
            except TeamspacesError as exc:
                raise TeamspacesError("Failed to find teamspace id.") from exc
            else:
                return teamspace_id

    return teamspace


def _normalize_member_id(member: Union[User, Member, TeamspaceUser, str]) -> str:
    """Normalize member arguments to a user id."""
    if isinstance(member, User):
        return member.id
    elif isinstance(member, (Member, TeamspaceUser)):
        return member.user_id
    elif isinstance(member, str) and member.startswith("usr_"):
        return member

    raise TeamspacesError("Failed to find user id.")


def create_teamspace(
    name: str,
    *,
    description: str = "New teamspace",
    visibility: TeamspaceVisibility = TeamspaceVisibility.PRIVATE,
) -> Teamspace:
    """Create a new teamspace in the current workspace.

    Parameters
    ----------
    name : str
        The name of the teamspace to create.
    description : str, optional
        Description of the teamspace to create.
    visibility : TeamspaceVisibility, optional
        Private is the default, but teamspaces may be public.

    Returns
    -------
    Teamspace

    Raises
    ------
    TeamspacesError:
        If the teamspace creation request failed.

    Examples
    --------
    >>> teamspace1 = teamspaces.create_teamspace(
    ...     "teamspace1",
    ...     description="Teamspace One",
    ...     visibility="private",
    ... )

    """
    create_teamspace_request = TeamspacesCreateRequest(
        name=name, description=description, visibility=visibility
    )
    try:
        create_teamspace_response = client.client.build(
            TeamspacesApi
        ).create_teamspaces(client.get_workspace_id(), create_teamspace_request)
    except ApiException as exc:
        raise TeamspacesError("The teamspace creation request failed.") from exc
    else:
        return create_teamspace_response.data


def delete_teamspace(
    teamspace: Union[Teamspace, str],
) -> None:
    """Create a new teamspace in the current workspace.

    Parameters
    ----------
    teamspace : Teamspace or str
        The teamspace to delete, identified by name or id.

    Raises
    ------
    TeamspacesError:
        If the teamspace deletion request failed.

    Examples
    --------
    >>> teamspaces.delete_teamspace("teamspace1")

    """
    try:
        client.client.build(TeamspacesApi).delete_teamspace(
            client.get_workspace_id(), getattr(teamspace, "teamspace_id", teamspace)
        )
    except ApiException as exc:
        raise TeamspacesError("The teamspace deletion request failed.") from exc


def get_teamspace(
    teamspace: Union[Teamspace, str],
) -> Teamspace:
    """Retrieve the representation of a teamspace.

    Parameters
    ----------
    teamspace : str
        The teamspace to retrieve, by name or id.

    Raises
    ------
    TeamspacesError:
        If the teamspace retrieval request failed.

    Examples
    --------
    >>> teamspaces.get_teamspace("teamspace1")
    Teamspace<>

    """
    try:
        resp = client.client.build(TeamspacesApi).get_teamspace(
            client.get_workspace_id(), getattr(teamspace, "teamspace_id", teamspace)
        )
    except ApiException as exc:
        raise TeamspacesError("The teamspace deletion request failed.") from exc
    else:
        return resp.data


def list_teamspaces(
    *,
    memberships: Optional[bool] = None,
    order_by: Optional[str] = None,
    order: Optional[str] = None,
) -> List[Teamspace]:
    """List teamspaces of the current workspace.

    This function can filter teamspaces based on the user's membership
    and control the sorting of the results.

    Parameters
    ----------
    memberships : bool, optional
        If True, returns teamspaces the user is a member of.
        If False, returns public teamspaces in the workspace that the
        user is NOT a member of.
        If not provided (default), the API's default behavior is used, which
        is typically to return all teamspaces the user has access to.
    order_by : str, optional
        The field to order the results by. Defaults to 'created_at'.
        Valid values include 'name', 'created_at', 'updated_at'.
    order : str, optional
        The sorting direction. Defaults to 'desc'.
        Valid values are 'asc', 'desc'.

    Returns
    -------
    list[Teamspace]
        A list of Teamspace objects.

    Raises
    ------
    TeamspacesError
        If the teamspaces listing request failed.

    Examples
    --------
    # List all teamspaces you are a member of
    >>> my_teamspaces = teamspaces.list_teamspaces(memberships=True)
    >>> [ts.name for ts in my_teamspaces]
    ["my-first-teamspace"]

    # List public teamspaces you are NOT a member of, ordered by name
    >>> public_teamspaces = teamspaces.list_teamspaces(
    ...     memberships=False, order_by="name", order="asc"
    ... )

    """
    try:
        resp = client.client.build(TeamspacesApi).list_teamspaces(
            client.get_workspace_id(),
            memberships=memberships,
            order_by=order_by,
            order=order,
        )
    except ApiException as exc:
        raise TeamspacesError("The teamspaces listing request failed.") from exc
    else:
        return resp.data


def list_teamspace_members(
    teamspace: Union[str, Teamspace],
    *,
    query: Optional[str] = None,
    page: Optional[int] = 1,
    per_page: Optional[int] = None,
) -> Pager[TeamspaceUser]:
    """List teamspace members.

    Parameters
    ----------
    teamspace : str or object
        The teamspace to retrieve, by name, id, or object.
    query : str, optional
        Match users by name or email address.

    Returns
    -------
    Pager for TeamspaceUsers

    Raises
    ------
    TeamspacesError:
        If the teamspace members listing request failed.

    Examples
    --------
    >>> for user in list_teamspace_members():
    ...     print(user.display_name)
    ...
    A User

    """
    teamspace_id = getattr(teamspace, "teamspace_id", teamspace)

    try:
        resp = Pager(
            client.client.build(TeamspacesApi).list_teamspace_users,
            client.get_workspace_id(),
            teamspace_id,
            search=query,
            per_page=per_page,
        )
        resp.call_page(page)
    except ApiException as exc:
        raise TeamspacesError("The teamspace users listing request failed.") from exc
    else:
        return resp


def add_teamspace_members(
    teamspace: Union[str, Teamspace],
    members: Union[Member, Sequence[Member]],
) -> None:
    """Add members to a teamspace.

    Parameters
    ----------
    teamspace : TeamspaceLike
        The teamspace, identified by name, id, or object.
    members : Member or list[Member]
        One or more members. The Member class is a thin wrapper
        around User, allowing a teamspace role to be attached.

    Raises
    ------
    TeamspacesError
        When members can not be added.

    Examples
    --------
    >>> add_teamspace_members("teamspace1", Member("usr_123"))

    Adds the user with id "usr_123" as a viewer to the teamspace named "teamspace1".

    """
    teamspace_id = getattr(teamspace, "teamspace_id", teamspace)

    if isinstance(members, Member):
        members = [members]

    teamspaces_api = client.build(TeamspacesApi)
    request = [
        TeamspaceUsersCreateRequestInner(
            user_id=getattr(m.user_id, "id", m.user_id), role=m.role
        )
        for m in members
    ]

    try:
        teamspaces_api.create_teamspace_users(
            client.get_workspace_id(),
            teamspace_id,
            request,
        )
    except ApiException as exc:
        raise TeamspacesError("Failed to add members.") from exc


def update_teamspace_member_roles(
    teamspace: Union[str, Teamspace],
    members: Union[Member, Sequence[Member]],
) -> None:
    """Update member roles for a teamspace.

    Parameters
    ----------
    teamspace : TeamspaceLike
        The teamspace, identified by name, id, or object.
    members : Member or list[Member]
        One or more members. The Member class is a thin wrapper
        around User, allowing a teamspace role to be attached.

    Raises
    ------
    TeamspacesError
        When members can not be updated.

    Examples
    --------
    >>> update_teamspace_member_roles(
    ...     "teamspace1",
    ...     Member("usr_123", role=TeamspaceRole.EDITOR)
    ... )

    Gives the user with id "usr_123" an editor role for the teamspace named "teamspace1".

    """
    teamspace_id = getattr(teamspace, "teamspace_id", teamspace)

    if isinstance(members, Member):
        members = [members]

    teamspaces_api = client.build(TeamspacesApi)
    request = [
        TeamspaceUsersBulkUpdateRequestInner(
            user_id=getattr(m.user_id, "id", m.user_id), role=m.role
        )
        for m in members
    ]

    try:
        teamspaces_api.update_teamspace_users(
            client.get_workspace_id(),
            teamspace_id,
            request,
        )
    except ApiException as exc:
        raise TeamspacesError("Failed to update members.") from exc


def remove_teamspace_members(
    teamspace: Union[str, Teamspace],
    members: Union[Union[str, User], Sequence[Union[str, User]]],
) -> None:
    """Remove members from a teamspace.

    Parameters
    ----------
    teamspace : TeamspaceLike
        The teamspace, identified by name, id, or object.
    members : str or User
        One or more members, identified by id or User obj.

    Raises
    ------
    TeamspacesError
        When members can not be removed.

    Examples
    --------
    >>> remove_teamspace_members("teamspace1", "usr_123")

    Removes the user with id "usr_123" from the teamspace named "teamspace1".

    """
    teamspace_id = getattr(teamspace, "teamspace_id", teamspace)

    if isinstance(members, (str, User)):
        members = [members]

    request = [getattr(m, "id", m) for m in members]
    teamspaces_api = client.build(TeamspacesApi)

    try:
        teamspaces_api.delete_teamspace_users(
            client.get_workspace_id(),
            teamspace_id,
            request,
        )
    except ApiException as exc:
        raise TeamspacesError("Failed to remove members.") from exc
