from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.record_usage_request import RecordUsageRequest
from ...models.record_usage_response import RecordUsageResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: RecordUsageRequest,
    x_service_token: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_service_token, Unset):
        headers["x-service-token"] = x_service_token

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/usage/events",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | RecordUsageResponse | None:
    if response.status_code == 200:
        response_200 = RecordUsageResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | RecordUsageResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: RecordUsageRequest,
    x_service_token: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | RecordUsageResponse]:
    """Record Usage

     Record a usage event.

    This endpoint is called by other Mushu services to report usage.
    Usage is recorded atomically and summaries are updated.
    Wallet is charged for billable metrics (amounts in micro-dollars).

    Args:
        x_service_token (None | str | Unset):
        body (RecordUsageRequest): Request to record a usage event.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RecordUsageResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        x_service_token=x_service_token,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: RecordUsageRequest,
    x_service_token: None | str | Unset = UNSET,
) -> HTTPValidationError | RecordUsageResponse | None:
    """Record Usage

     Record a usage event.

    This endpoint is called by other Mushu services to report usage.
    Usage is recorded atomically and summaries are updated.
    Wallet is charged for billable metrics (amounts in micro-dollars).

    Args:
        x_service_token (None | str | Unset):
        body (RecordUsageRequest): Request to record a usage event.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RecordUsageResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        x_service_token=x_service_token,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: RecordUsageRequest,
    x_service_token: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | RecordUsageResponse]:
    """Record Usage

     Record a usage event.

    This endpoint is called by other Mushu services to report usage.
    Usage is recorded atomically and summaries are updated.
    Wallet is charged for billable metrics (amounts in micro-dollars).

    Args:
        x_service_token (None | str | Unset):
        body (RecordUsageRequest): Request to record a usage event.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RecordUsageResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        x_service_token=x_service_token,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: RecordUsageRequest,
    x_service_token: None | str | Unset = UNSET,
) -> HTTPValidationError | RecordUsageResponse | None:
    """Record Usage

     Record a usage event.

    This endpoint is called by other Mushu services to report usage.
    Usage is recorded atomically and summaries are updated.
    Wallet is charged for billable metrics (amounts in micro-dollars).

    Args:
        x_service_token (None | str | Unset):
        body (RecordUsageRequest): Request to record a usage event.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RecordUsageResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_service_token=x_service_token,
        )
    ).parsed
