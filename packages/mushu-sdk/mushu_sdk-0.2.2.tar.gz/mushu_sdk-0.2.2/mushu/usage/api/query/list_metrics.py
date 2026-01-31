from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    service: None | str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_service: None | str | Unset
    if isinstance(service, Unset):
        json_service = UNSET
    else:
        json_service = service
    params["service"] = json_service

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/metrics",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = response.json()
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
) -> Response[Any | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    service: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """List Metrics

     List all available metrics and their prices.

    Prices are in micro-dollars (1 USD = 1,000,000 micros).
    Example: $0.005 = 5,000 micros

    This is a public endpoint - no authentication required.

    Args:
        service (None | str | Unset): Filter by service name

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        service=service,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    service: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """List Metrics

     List all available metrics and their prices.

    Prices are in micro-dollars (1 USD = 1,000,000 micros).
    Example: $0.005 = 5,000 micros

    This is a public endpoint - no authentication required.

    Args:
        service (None | str | Unset): Filter by service name

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        service=service,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    service: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """List Metrics

     List all available metrics and their prices.

    Prices are in micro-dollars (1 USD = 1,000,000 micros).
    Example: $0.005 = 5,000 micros

    This is a public endpoint - no authentication required.

    Args:
        service (None | str | Unset): Filter by service name

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        service=service,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    service: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """List Metrics

     List all available metrics and their prices.

    Prices are in micro-dollars (1 USD = 1,000,000 micros).
    Example: $0.005 = 5,000 micros

    This is a public endpoint - no authentication required.

    Args:
        service (None | str | Unset): Filter by service name

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            service=service,
        )
    ).parsed
