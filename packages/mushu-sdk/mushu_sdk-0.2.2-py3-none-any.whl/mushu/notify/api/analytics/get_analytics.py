from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.analytics_response import AnalyticsResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    app_id: str,
    *,
    days: int | Unset = 7,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization

    if not isinstance(x_api_key, Unset):
        headers["X-API-Key"] = x_api_key

    params: dict[str, Any] = {}

    params["days"] = days

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/apps/{app_id}/analytics".format(
            app_id=quote(str(app_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AnalyticsResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = AnalyticsResponse.from_dict(response.json())

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
) -> Response[AnalyticsResponse | HTTPValidationError]:
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
    days: int | Unset = 7,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Response[AnalyticsResponse | HTTPValidationError]:
    """Get Analytics

     Get notification analytics for an app.

    Returns aggregated stats for push and email notifications
    over the specified time period.

    Args:
        app_id (str):
        days (int | Unset): Number of days to analyze Default: 7.
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AnalyticsResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        days=days,
        authorization=authorization,
        x_api_key=x_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    app_id: str,
    *,
    client: AuthenticatedClient | Client,
    days: int | Unset = 7,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> AnalyticsResponse | HTTPValidationError | None:
    """Get Analytics

     Get notification analytics for an app.

    Returns aggregated stats for push and email notifications
    over the specified time period.

    Args:
        app_id (str):
        days (int | Unset): Number of days to analyze Default: 7.
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AnalyticsResponse | HTTPValidationError
    """

    return sync_detailed(
        app_id=app_id,
        client=client,
        days=days,
        authorization=authorization,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    app_id: str,
    *,
    client: AuthenticatedClient | Client,
    days: int | Unset = 7,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Response[AnalyticsResponse | HTTPValidationError]:
    """Get Analytics

     Get notification analytics for an app.

    Returns aggregated stats for push and email notifications
    over the specified time period.

    Args:
        app_id (str):
        days (int | Unset): Number of days to analyze Default: 7.
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AnalyticsResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        days=days,
        authorization=authorization,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    app_id: str,
    *,
    client: AuthenticatedClient | Client,
    days: int | Unset = 7,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> AnalyticsResponse | HTTPValidationError | None:
    """Get Analytics

     Get notification analytics for an app.

    Returns aggregated stats for push and email notifications
    over the specified time period.

    Args:
        app_id (str):
        days (int | Unset): Number of days to analyze Default: 7.
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AnalyticsResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            app_id=app_id,
            client=client,
            days=days,
            authorization=authorization,
            x_api_key=x_api_key,
        )
    ).parsed
