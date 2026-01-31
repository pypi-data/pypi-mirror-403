from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_email_invite_request import CreateEmailInviteRequest
from ...models.http_validation_error import HTTPValidationError
from ...models.org_invite import OrgInvite
from ...types import Response


def _get_kwargs(
    org_id: str,
    *,
    body: CreateEmailInviteRequest,
    authorization: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["authorization"] = authorization

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/orgs/{org_id}/invites/email".format(
            org_id=quote(str(org_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | OrgInvite | None:
    if response.status_code == 200:
        response_200 = OrgInvite.from_dict(response.json())

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
) -> Response[HTTPValidationError | OrgInvite]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CreateEmailInviteRequest,
    authorization: str,
) -> Response[HTTPValidationError | OrgInvite]:
    """Create Email Invite

     Create an email invite to an organization. Requires admin role.

    Args:
        org_id (str):
        authorization (str):
        body (CreateEmailInviteRequest): Request to invite a user by email.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | OrgInvite]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        body=body,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CreateEmailInviteRequest,
    authorization: str,
) -> HTTPValidationError | OrgInvite | None:
    """Create Email Invite

     Create an email invite to an organization. Requires admin role.

    Args:
        org_id (str):
        authorization (str):
        body (CreateEmailInviteRequest): Request to invite a user by email.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | OrgInvite
    """

    return sync_detailed(
        org_id=org_id,
        client=client,
        body=body,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CreateEmailInviteRequest,
    authorization: str,
) -> Response[HTTPValidationError | OrgInvite]:
    """Create Email Invite

     Create an email invite to an organization. Requires admin role.

    Args:
        org_id (str):
        authorization (str):
        body (CreateEmailInviteRequest): Request to invite a user by email.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | OrgInvite]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        body=body,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CreateEmailInviteRequest,
    authorization: str,
) -> HTTPValidationError | OrgInvite | None:
    """Create Email Invite

     Create an email invite to an organization. Requires admin role.

    Args:
        org_id (str):
        authorization (str):
        body (CreateEmailInviteRequest): Request to invite a user by email.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | OrgInvite
    """

    return (
        await asyncio_detailed(
            org_id=org_id,
            client=client,
            body=body,
            authorization=authorization,
        )
    ).parsed
