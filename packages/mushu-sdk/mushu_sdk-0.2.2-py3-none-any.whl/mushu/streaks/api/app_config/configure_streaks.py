from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.app_config import AppConfig
from ...models.configure_streaks_request import ConfigureStreaksRequest
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    app_id: str,
    *,
    body: ConfigureStreaksRequest,
    authorization: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["authorization"] = authorization

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/apps/{app_id}/streaks-config".format(
            app_id=quote(str(app_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AppConfig | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = AppConfig.from_dict(response.json())

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
) -> Response[AppConfig | HTTPValidationError]:
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
    body: ConfigureStreaksRequest,
    authorization: str,
) -> Response[AppConfig | HTTPValidationError]:
    """Configure App Streaks

     Configure app streak settings.

    Args:
        app_id (str):
        authorization (str):
        body (ConfigureStreaksRequest): Request to configure app streak settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AppConfig | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        body=body,
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
    body: ConfigureStreaksRequest,
    authorization: str,
) -> AppConfig | HTTPValidationError | None:
    """Configure App Streaks

     Configure app streak settings.

    Args:
        app_id (str):
        authorization (str):
        body (ConfigureStreaksRequest): Request to configure app streak settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AppConfig | HTTPValidationError
    """

    return sync_detailed(
        app_id=app_id,
        client=client,
        body=body,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    app_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: ConfigureStreaksRequest,
    authorization: str,
) -> Response[AppConfig | HTTPValidationError]:
    """Configure App Streaks

     Configure app streak settings.

    Args:
        app_id (str):
        authorization (str):
        body (ConfigureStreaksRequest): Request to configure app streak settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AppConfig | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        body=body,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    app_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: ConfigureStreaksRequest,
    authorization: str,
) -> AppConfig | HTTPValidationError | None:
    """Configure App Streaks

     Configure app streak settings.

    Args:
        app_id (str):
        authorization (str):
        body (ConfigureStreaksRequest): Request to configure app streak settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AppConfig | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            app_id=app_id,
            client=client,
            body=body,
            authorization=authorization,
        )
    ).parsed
