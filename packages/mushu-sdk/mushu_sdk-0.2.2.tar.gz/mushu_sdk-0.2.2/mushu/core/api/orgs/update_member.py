from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.org_member import OrgMember
from ...models.update_member_request import UpdateMemberRequest
from ...types import Response


def _get_kwargs(
    org_id: str,
    member_user_id: str,
    *,
    body: UpdateMemberRequest,
    authorization: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["authorization"] = authorization

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/orgs/{org_id}/members/{member_user_id}".format(
            org_id=quote(str(org_id), safe=""),
            member_user_id=quote(str(member_user_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | OrgMember | None:
    if response.status_code == 200:
        response_200 = OrgMember.from_dict(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | OrgMember]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    org_id: str,
    member_user_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateMemberRequest,
    authorization: str,
) -> Response[HTTPValidationError | OrgMember]:
    """Update Member

     Update member role. Requires admin role.

    Args:
        org_id (str):
        member_user_id (str):
        authorization (str):
        body (UpdateMemberRequest): Request to update a member's role.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | OrgMember]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        member_user_id=member_user_id,
        body=body,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    org_id: str,
    member_user_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateMemberRequest,
    authorization: str,
) -> HTTPValidationError | OrgMember | None:
    """Update Member

     Update member role. Requires admin role.

    Args:
        org_id (str):
        member_user_id (str):
        authorization (str):
        body (UpdateMemberRequest): Request to update a member's role.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | OrgMember
    """

    return sync_detailed(
        org_id=org_id,
        member_user_id=member_user_id,
        client=client,
        body=body,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    org_id: str,
    member_user_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateMemberRequest,
    authorization: str,
) -> Response[HTTPValidationError | OrgMember]:
    """Update Member

     Update member role. Requires admin role.

    Args:
        org_id (str):
        member_user_id (str):
        authorization (str):
        body (UpdateMemberRequest): Request to update a member's role.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | OrgMember]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        member_user_id=member_user_id,
        body=body,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    org_id: str,
    member_user_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateMemberRequest,
    authorization: str,
) -> HTTPValidationError | OrgMember | None:
    """Update Member

     Update member role. Requires admin role.

    Args:
        org_id (str):
        member_user_id (str):
        authorization (str):
        body (UpdateMemberRequest): Request to update a member's role.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | OrgMember
    """

    return (
        await asyncio_detailed(
            org_id=org_id,
            member_user_id=member_user_id,
            client=client,
            body=body,
            authorization=authorization,
        )
    ).parsed
