from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.timezone_request import TimezoneRequest
from ...models.timezone_response import TimezoneResponse
from ...types import Response


def _get_kwargs(
    *,
    body: TimezoneRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/location/timezone",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TimezoneResponse | None:
    if response.status_code == 200:
        response_200 = TimezoneResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | TimezoneResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TimezoneRequest,
) -> Response[HTTPValidationError | TimezoneResponse]:
    """Lookup Timezone

     Look up timezone from coordinates.

    Returns the IANA timezone name and current UTC offset for the given coordinates.
    This is a free endpoint that does not require authentication.

    Uses the timezonefinder library for local lookup (no external API calls).

    Args:
        body (TimezoneRequest): Request to lookup timezone from coordinates.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TimezoneResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: TimezoneRequest,
) -> HTTPValidationError | TimezoneResponse | None:
    """Lookup Timezone

     Look up timezone from coordinates.

    Returns the IANA timezone name and current UTC offset for the given coordinates.
    This is a free endpoint that does not require authentication.

    Uses the timezonefinder library for local lookup (no external API calls).

    Args:
        body (TimezoneRequest): Request to lookup timezone from coordinates.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TimezoneResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TimezoneRequest,
) -> Response[HTTPValidationError | TimezoneResponse]:
    """Lookup Timezone

     Look up timezone from coordinates.

    Returns the IANA timezone name and current UTC offset for the given coordinates.
    This is a free endpoint that does not require authentication.

    Uses the timezonefinder library for local lookup (no external API calls).

    Args:
        body (TimezoneRequest): Request to lookup timezone from coordinates.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TimezoneResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: TimezoneRequest,
) -> HTTPValidationError | TimezoneResponse | None:
    """Lookup Timezone

     Look up timezone from coordinates.

    Returns the IANA timezone name and current UTC offset for the given coordinates.
    This is a free endpoint that does not require authentication.

    Uses the timezonefinder library for local lookup (no external API calls).

    Args:
        body (TimezoneRequest): Request to lookup timezone from coordinates.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TimezoneResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
