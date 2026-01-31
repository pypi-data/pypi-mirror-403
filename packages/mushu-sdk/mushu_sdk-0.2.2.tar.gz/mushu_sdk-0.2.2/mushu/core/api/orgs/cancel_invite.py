from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.cancel_invite_response_cancel_invite import CancelInviteResponseCancelInvite
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    org_id: str,
    invite_id: str,
    *,
    authorization: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["authorization"] = authorization

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/orgs/{org_id}/invites/{invite_id}".format(
            org_id=quote(str(org_id), safe=""),
            invite_id=quote(str(invite_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CancelInviteResponseCancelInvite | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = CancelInviteResponseCancelInvite.from_dict(response.json())

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
) -> Response[CancelInviteResponseCancelInvite | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    org_id: str,
    invite_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: str,
) -> Response[CancelInviteResponseCancelInvite | HTTPValidationError]:
    """Cancel Invite

     Cancel a pending invite. Requires admin role.

    Args:
        org_id (str):
        invite_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CancelInviteResponseCancelInvite | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        invite_id=invite_id,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    org_id: str,
    invite_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: str,
) -> CancelInviteResponseCancelInvite | HTTPValidationError | None:
    """Cancel Invite

     Cancel a pending invite. Requires admin role.

    Args:
        org_id (str):
        invite_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CancelInviteResponseCancelInvite | HTTPValidationError
    """

    return sync_detailed(
        org_id=org_id,
        invite_id=invite_id,
        client=client,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    org_id: str,
    invite_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: str,
) -> Response[CancelInviteResponseCancelInvite | HTTPValidationError]:
    """Cancel Invite

     Cancel a pending invite. Requires admin role.

    Args:
        org_id (str):
        invite_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CancelInviteResponseCancelInvite | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        invite_id=invite_id,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    org_id: str,
    invite_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: str,
) -> CancelInviteResponseCancelInvite | HTTPValidationError | None:
    """Cancel Invite

     Cancel a pending invite. Requires admin role.

    Args:
        org_id (str):
        invite_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CancelInviteResponseCancelInvite | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            org_id=org_id,
            invite_id=invite_id,
            client=client,
            authorization=authorization,
        )
    ).parsed
