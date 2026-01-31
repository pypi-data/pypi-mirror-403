from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.invite_list_response import InviteListResponse
from ...models.invite_status import InviteStatus
from ...types import UNSET, Response, Unset


def _get_kwargs(
    org_id: str,
    *,
    status: InviteStatus | None | Unset = UNSET,
    authorization: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["authorization"] = authorization

    params: dict[str, Any] = {}

    json_status: None | str | Unset
    if isinstance(status, Unset):
        json_status = UNSET
    elif isinstance(status, InviteStatus):
        json_status = status.value
    else:
        json_status = status
    params["status"] = json_status

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/orgs/{org_id}/invites".format(
            org_id=quote(str(org_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | InviteListResponse | None:
    if response.status_code == 200:
        response_200 = InviteListResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | InviteListResponse]:
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
    status: InviteStatus | None | Unset = UNSET,
    authorization: str,
) -> Response[HTTPValidationError | InviteListResponse]:
    """List Invites

     List invites for an organization. Requires admin role.

    Args:
        org_id (str):
        status (InviteStatus | None | Unset):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | InviteListResponse]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        status=status,
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
    status: InviteStatus | None | Unset = UNSET,
    authorization: str,
) -> HTTPValidationError | InviteListResponse | None:
    """List Invites

     List invites for an organization. Requires admin role.

    Args:
        org_id (str):
        status (InviteStatus | None | Unset):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | InviteListResponse
    """

    return sync_detailed(
        org_id=org_id,
        client=client,
        status=status,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    status: InviteStatus | None | Unset = UNSET,
    authorization: str,
) -> Response[HTTPValidationError | InviteListResponse]:
    """List Invites

     List invites for an organization. Requires admin role.

    Args:
        org_id (str):
        status (InviteStatus | None | Unset):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | InviteListResponse]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        status=status,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    status: InviteStatus | None | Unset = UNSET,
    authorization: str,
) -> HTTPValidationError | InviteListResponse | None:
    """List Invites

     List invites for an organization. Requires admin role.

    Args:
        org_id (str):
        status (InviteStatus | None | Unset):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | InviteListResponse
    """

    return (
        await asyncio_detailed(
            org_id=org_id,
            client=client,
            status=status,
            authorization=authorization,
        )
    ).parsed
