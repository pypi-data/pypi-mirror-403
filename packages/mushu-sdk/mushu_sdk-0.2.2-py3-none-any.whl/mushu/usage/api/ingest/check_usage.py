from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.usage_check_request import UsageCheckRequest
from ...models.usage_check_response import UsageCheckResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: UsageCheckRequest,
    x_service_token: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_service_token, Unset):
        headers["x-service-token"] = x_service_token

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/usage/check",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | UsageCheckResponse | None:
    if response.status_code == 200:
        response_200 = UsageCheckResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | UsageCheckResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: UsageCheckRequest,
    x_service_token: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | UsageCheckResponse]:
    """Check Usage

     Pre-check if an operation is allowed under quota limits.

    Services can call this before performing an operation to check
    if it would exceed quotas. This does NOT record usage.

    Args:
        x_service_token (None | str | Unset):
        body (UsageCheckRequest): Pre-check if operation is allowed under quota.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | UsageCheckResponse]
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
    body: UsageCheckRequest,
    x_service_token: None | str | Unset = UNSET,
) -> HTTPValidationError | UsageCheckResponse | None:
    """Check Usage

     Pre-check if an operation is allowed under quota limits.

    Services can call this before performing an operation to check
    if it would exceed quotas. This does NOT record usage.

    Args:
        x_service_token (None | str | Unset):
        body (UsageCheckRequest): Pre-check if operation is allowed under quota.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | UsageCheckResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        x_service_token=x_service_token,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: UsageCheckRequest,
    x_service_token: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | UsageCheckResponse]:
    """Check Usage

     Pre-check if an operation is allowed under quota limits.

    Services can call this before performing an operation to check
    if it would exceed quotas. This does NOT record usage.

    Args:
        x_service_token (None | str | Unset):
        body (UsageCheckRequest): Pre-check if operation is allowed under quota.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | UsageCheckResponse]
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
    body: UsageCheckRequest,
    x_service_token: None | str | Unset = UNSET,
) -> HTTPValidationError | UsageCheckResponse | None:
    """Check Usage

     Pre-check if an operation is allowed under quota limits.

    Services can call this before performing an operation to check
    if it would exceed quotas. This does NOT record usage.

    Args:
        x_service_token (None | str | Unset):
        body (UsageCheckRequest): Pre-check if operation is allowed under quota.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | UsageCheckResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_service_token=x_service_token,
        )
    ).parsed
