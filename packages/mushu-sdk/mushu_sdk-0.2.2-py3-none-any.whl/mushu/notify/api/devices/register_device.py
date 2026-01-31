from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.device import Device
from ...models.http_validation_error import HTTPValidationError
from ...models.register_device_request import RegisterDeviceRequest
from ...types import UNSET, Response, Unset


def _get_kwargs(
    app_id: str,
    *,
    body: RegisterDeviceRequest,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization

    if not isinstance(x_api_key, Unset):
        headers["X-API-Key"] = x_api_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/apps/{app_id}/devices".format(
            app_id=quote(str(app_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Device | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = Device.from_dict(response.json())

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
) -> Response[Device | HTTPValidationError]:
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
    body: RegisterDeviceRequest,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Response[Device | HTTPValidationError]:
    """Register Device

     Register a device token for push notifications.

    If the token already exists for another user, it will be reassigned.

    Args:
        app_id (str):
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):
        body (RegisterDeviceRequest): Request to register a device.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Device | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        body=body,
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
    body: RegisterDeviceRequest,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Device | HTTPValidationError | None:
    """Register Device

     Register a device token for push notifications.

    If the token already exists for another user, it will be reassigned.

    Args:
        app_id (str):
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):
        body (RegisterDeviceRequest): Request to register a device.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Device | HTTPValidationError
    """

    return sync_detailed(
        app_id=app_id,
        client=client,
        body=body,
        authorization=authorization,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    app_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: RegisterDeviceRequest,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Response[Device | HTTPValidationError]:
    """Register Device

     Register a device token for push notifications.

    If the token already exists for another user, it will be reassigned.

    Args:
        app_id (str):
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):
        body (RegisterDeviceRequest): Request to register a device.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Device | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        body=body,
        authorization=authorization,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    app_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: RegisterDeviceRequest,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Device | HTTPValidationError | None:
    """Register Device

     Register a device token for push notifications.

    If the token already exists for another user, it will be reassigned.

    Args:
        app_id (str):
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):
        body (RegisterDeviceRequest): Request to register a device.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Device | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            app_id=app_id,
            client=client,
            body=body,
            authorization=authorization,
            x_api_key=x_api_key,
        )
    ).parsed
