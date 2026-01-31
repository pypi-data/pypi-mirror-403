from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.app_usage_summary import AppUsageSummary
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    app_id: str,
    *,
    period: None | str | Unset = UNSET,
    authorization: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["authorization"] = authorization

    params: dict[str, Any] = {}

    json_period: None | str | Unset
    if isinstance(period, Unset):
        json_period = UNSET
    else:
        json_period = period
    params["period"] = json_period

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/apps/{app_id}/usage".format(
            app_id=quote(str(app_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AppUsageSummary | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = AppUsageSummary.from_dict(response.json())

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
) -> Response[AppUsageSummary | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    app_id: str,
    *,
    client: AuthenticatedClient | Client,
    period: None | str | Unset = UNSET,
    authorization: str,
) -> Response[AppUsageSummary | HTTPValidationError]:
    """Get App Usage

     Get usage summary for an app.

    Returns usage breakdown for a specific app.

    Args:
        app_id (str):
        period (None | str | Unset): Period in YYYY-MM format
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AppUsageSummary | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        period=period,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    app_id: str,
    *,
    client: AuthenticatedClient | Client,
    period: None | str | Unset = UNSET,
    authorization: str,
) -> AppUsageSummary | HTTPValidationError | None:
    """Get App Usage

     Get usage summary for an app.

    Returns usage breakdown for a specific app.

    Args:
        app_id (str):
        period (None | str | Unset): Period in YYYY-MM format
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AppUsageSummary | HTTPValidationError
    """

    return sync_detailed(
        app_id=app_id,
        client=client,
        period=period,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    app_id: str,
    *,
    client: AuthenticatedClient | Client,
    period: None | str | Unset = UNSET,
    authorization: str,
) -> Response[AppUsageSummary | HTTPValidationError]:
    """Get App Usage

     Get usage summary for an app.

    Returns usage breakdown for a specific app.

    Args:
        app_id (str):
        period (None | str | Unset): Period in YYYY-MM format
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AppUsageSummary | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        period=period,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    app_id: str,
    *,
    client: AuthenticatedClient | Client,
    period: None | str | Unset = UNSET,
    authorization: str,
) -> AppUsageSummary | HTTPValidationError | None:
    """Get App Usage

     Get usage summary for an app.

    Returns usage breakdown for a specific app.

    Args:
        app_id (str):
        period (None | str | Unset): Period in YYYY-MM format
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AppUsageSummary | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            app_id=app_id,
            client=client,
            period=period,
            authorization=authorization,
        )
    ).parsed
