from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.unregister_device_response_unregister_device import (
    UnregisterDeviceResponseUnregisterDevice,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    app_id: str,
    token: str,
    *,
    user_id: str,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization

    if not isinstance(x_api_key, Unset):
        headers["X-API-Key"] = x_api_key

    params: dict[str, Any] = {}

    params["user_id"] = user_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/apps/{app_id}/devices/{token}".format(
            app_id=quote(str(app_id), safe=""),
            token=quote(str(token), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | UnregisterDeviceResponseUnregisterDevice | None:
    if response.status_code == 200:
        response_200 = UnregisterDeviceResponseUnregisterDevice.from_dict(response.json())

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
) -> Response[HTTPValidationError | UnregisterDeviceResponseUnregisterDevice]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    app_id: str,
    token: str,
    *,
    client: AuthenticatedClient | Client,
    user_id: str,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | UnregisterDeviceResponseUnregisterDevice]:
    """Unregister Device

     Unregister a device token.

    Args:
        app_id (str):
        token (str):
        user_id (str): User ID that owns the device
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | UnregisterDeviceResponseUnregisterDevice]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        token=token,
        user_id=user_id,
        authorization=authorization,
        x_api_key=x_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    app_id: str,
    token: str,
    *,
    client: AuthenticatedClient | Client,
    user_id: str,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> HTTPValidationError | UnregisterDeviceResponseUnregisterDevice | None:
    """Unregister Device

     Unregister a device token.

    Args:
        app_id (str):
        token (str):
        user_id (str): User ID that owns the device
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | UnregisterDeviceResponseUnregisterDevice
    """

    return sync_detailed(
        app_id=app_id,
        token=token,
        client=client,
        user_id=user_id,
        authorization=authorization,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    app_id: str,
    token: str,
    *,
    client: AuthenticatedClient | Client,
    user_id: str,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | UnregisterDeviceResponseUnregisterDevice]:
    """Unregister Device

     Unregister a device token.

    Args:
        app_id (str):
        token (str):
        user_id (str): User ID that owns the device
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | UnregisterDeviceResponseUnregisterDevice]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        token=token,
        user_id=user_id,
        authorization=authorization,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    app_id: str,
    token: str,
    *,
    client: AuthenticatedClient | Client,
    user_id: str,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> HTTPValidationError | UnregisterDeviceResponseUnregisterDevice | None:
    """Unregister Device

     Unregister a device token.

    Args:
        app_id (str):
        token (str):
        user_id (str): User ID that owns the device
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | UnregisterDeviceResponseUnregisterDevice
    """

    return (
        await asyncio_detailed(
            app_id=app_id,
            token=token,
            client=client,
            user_id=user_id,
            authorization=authorization,
            x_api_key=x_api_key,
        )
    ).parsed
