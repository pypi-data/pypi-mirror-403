from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.invite_validation_response import InviteValidationResponse
from ...types import Response


def _get_kwargs(
    invite_token: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/invites/{invite_token}/validate".format(
            invite_token=quote(str(invite_token), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | InviteValidationResponse | None:
    if response.status_code == 200:
        response_200 = InviteValidationResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | InviteValidationResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    invite_token: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[HTTPValidationError | InviteValidationResponse]:
    """Validate Invite

     Validate an invite token (public endpoint).
    Returns invite details if valid, or error message if invalid.

    Args:
        invite_token (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | InviteValidationResponse]
    """

    kwargs = _get_kwargs(
        invite_token=invite_token,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    invite_token: str,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | InviteValidationResponse | None:
    """Validate Invite

     Validate an invite token (public endpoint).
    Returns invite details if valid, or error message if invalid.

    Args:
        invite_token (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | InviteValidationResponse
    """

    return sync_detailed(
        invite_token=invite_token,
        client=client,
    ).parsed


async def asyncio_detailed(
    invite_token: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[HTTPValidationError | InviteValidationResponse]:
    """Validate Invite

     Validate an invite token (public endpoint).
    Returns invite details if valid, or error message if invalid.

    Args:
        invite_token (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | InviteValidationResponse]
    """

    kwargs = _get_kwargs(
        invite_token=invite_token,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    invite_token: str,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | InviteValidationResponse | None:
    """Validate Invite

     Validate an invite token (public endpoint).
    Returns invite details if valid, or error message if invalid.

    Args:
        invite_token (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | InviteValidationResponse
    """

    return (
        await asyncio_detailed(
            invite_token=invite_token,
            client=client,
        )
    ).parsed
