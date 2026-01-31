from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.send_notify_request import SendNotifyRequest
from ...models.send_unified_notify_response_send_unified_notify import (
    SendUnifiedNotifyResponseSendUnifiedNotify,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    app_id: str,
    *,
    body: SendNotifyRequest,
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
        "url": "/apps/{app_id}/notify/unified".format(
            app_id=quote(str(app_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | SendUnifiedNotifyResponseSendUnifiedNotify | None:
    if response.status_code == 200:
        response_200 = SendUnifiedNotifyResponseSendUnifiedNotify.from_dict(response.json())

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
) -> Response[HTTPValidationError | SendUnifiedNotifyResponseSendUnifiedNotify]:
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
    body: SendNotifyRequest,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | SendUnifiedNotifyResponseSendUnifiedNotify]:
    """Send Unified Notify

     Send notification via specified channel(s).

    Supports:
    - push: Send push notification to user's devices
    - email: Send email to user's registered email contacts
    - all: Send via both channels

    Usage is metered via mushu-usage and charged to org wallet.

    Args:
        app_id (str):
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):
        body (SendNotifyRequest): Unified request to send notification via any channel.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SendUnifiedNotifyResponseSendUnifiedNotify]
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
    body: SendNotifyRequest,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> HTTPValidationError | SendUnifiedNotifyResponseSendUnifiedNotify | None:
    """Send Unified Notify

     Send notification via specified channel(s).

    Supports:
    - push: Send push notification to user's devices
    - email: Send email to user's registered email contacts
    - all: Send via both channels

    Usage is metered via mushu-usage and charged to org wallet.

    Args:
        app_id (str):
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):
        body (SendNotifyRequest): Unified request to send notification via any channel.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SendUnifiedNotifyResponseSendUnifiedNotify
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
    body: SendNotifyRequest,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | SendUnifiedNotifyResponseSendUnifiedNotify]:
    """Send Unified Notify

     Send notification via specified channel(s).

    Supports:
    - push: Send push notification to user's devices
    - email: Send email to user's registered email contacts
    - all: Send via both channels

    Usage is metered via mushu-usage and charged to org wallet.

    Args:
        app_id (str):
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):
        body (SendNotifyRequest): Unified request to send notification via any channel.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SendUnifiedNotifyResponseSendUnifiedNotify]
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
    body: SendNotifyRequest,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> HTTPValidationError | SendUnifiedNotifyResponseSendUnifiedNotify | None:
    """Send Unified Notify

     Send notification via specified channel(s).

    Supports:
    - push: Send push notification to user's devices
    - email: Send email to user's registered email contacts
    - all: Send via both channels

    Usage is metered via mushu-usage and charged to org wallet.

    Args:
        app_id (str):
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):
        body (SendNotifyRequest): Unified request to send notification via any channel.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SendUnifiedNotifyResponseSendUnifiedNotify
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
