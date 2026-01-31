from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.apple_s2s_notifications_response_apple_s2s_notifications import (
    AppleS2SNotificationsResponseAppleS2SNotifications,
)
from ...models.apple_s2s_request import AppleS2SRequest
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: AppleS2SRequest,
    app_id: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    json_app_id: None | str | Unset
    if isinstance(app_id, Unset):
        json_app_id = UNSET
    else:
        json_app_id = app_id
    params["app_id"] = json_app_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/auth/apple/notifications",
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AppleS2SNotificationsResponseAppleS2SNotifications | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = AppleS2SNotificationsResponseAppleS2SNotifications.from_dict(response.json())

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
) -> Response[AppleS2SNotificationsResponseAppleS2SNotifications | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AppleS2SRequest,
    app_id: None | str | Unset = UNSET,
) -> Response[AppleS2SNotificationsResponseAppleS2SNotifications | HTTPValidationError]:
    """Apple S2S Notifications

     Handle Apple Server-to-Server notifications for account lifecycle events.

    Apple sends these notifications when:
    - account-delete: User deletes their Apple ID
    - consent-revoked: User revokes app consent in Settings
    - email-disabled: User disables email forwarding via private relay
    - email-enabled: User enables email forwarding via private relay

    For multi-tenant deployments, customer apps should configure their Apple webhook
    URL with ?app_id={app_id} to route notifications to the correct user.

    Note: This endpoint has no authentication header - Apple doesn't send one.
    We validate the JWT signature to authenticate the request.

    Args:
        app_id (None | str | Unset): App ID for multi-tenant S2S notifications
        body (AppleS2SRequest): Apple S2S notification request body.

            Apple sends notifications wrapped in a JSON object with a 'payload' field
            containing the JWT, not as a raw JWT.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AppleS2SNotificationsResponseAppleS2SNotifications | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        app_id=app_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: AppleS2SRequest,
    app_id: None | str | Unset = UNSET,
) -> AppleS2SNotificationsResponseAppleS2SNotifications | HTTPValidationError | None:
    """Apple S2S Notifications

     Handle Apple Server-to-Server notifications for account lifecycle events.

    Apple sends these notifications when:
    - account-delete: User deletes their Apple ID
    - consent-revoked: User revokes app consent in Settings
    - email-disabled: User disables email forwarding via private relay
    - email-enabled: User enables email forwarding via private relay

    For multi-tenant deployments, customer apps should configure their Apple webhook
    URL with ?app_id={app_id} to route notifications to the correct user.

    Note: This endpoint has no authentication header - Apple doesn't send one.
    We validate the JWT signature to authenticate the request.

    Args:
        app_id (None | str | Unset): App ID for multi-tenant S2S notifications
        body (AppleS2SRequest): Apple S2S notification request body.

            Apple sends notifications wrapped in a JSON object with a 'payload' field
            containing the JWT, not as a raw JWT.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AppleS2SNotificationsResponseAppleS2SNotifications | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
        app_id=app_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AppleS2SRequest,
    app_id: None | str | Unset = UNSET,
) -> Response[AppleS2SNotificationsResponseAppleS2SNotifications | HTTPValidationError]:
    """Apple S2S Notifications

     Handle Apple Server-to-Server notifications for account lifecycle events.

    Apple sends these notifications when:
    - account-delete: User deletes their Apple ID
    - consent-revoked: User revokes app consent in Settings
    - email-disabled: User disables email forwarding via private relay
    - email-enabled: User enables email forwarding via private relay

    For multi-tenant deployments, customer apps should configure their Apple webhook
    URL with ?app_id={app_id} to route notifications to the correct user.

    Note: This endpoint has no authentication header - Apple doesn't send one.
    We validate the JWT signature to authenticate the request.

    Args:
        app_id (None | str | Unset): App ID for multi-tenant S2S notifications
        body (AppleS2SRequest): Apple S2S notification request body.

            Apple sends notifications wrapped in a JSON object with a 'payload' field
            containing the JWT, not as a raw JWT.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AppleS2SNotificationsResponseAppleS2SNotifications | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        app_id=app_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: AppleS2SRequest,
    app_id: None | str | Unset = UNSET,
) -> AppleS2SNotificationsResponseAppleS2SNotifications | HTTPValidationError | None:
    """Apple S2S Notifications

     Handle Apple Server-to-Server notifications for account lifecycle events.

    Apple sends these notifications when:
    - account-delete: User deletes their Apple ID
    - consent-revoked: User revokes app consent in Settings
    - email-disabled: User disables email forwarding via private relay
    - email-enabled: User enables email forwarding via private relay

    For multi-tenant deployments, customer apps should configure their Apple webhook
    URL with ?app_id={app_id} to route notifications to the correct user.

    Note: This endpoint has no authentication header - Apple doesn't send one.
    We validate the JWT signature to authenticate the request.

    Args:
        app_id (None | str | Unset): App ID for multi-tenant S2S notifications
        body (AppleS2SRequest): Apple S2S notification request body.

            Apple sends notifications wrapped in a JSON object with a 'payload' field
            containing the JWT, not as a raw JWT.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AppleS2SNotificationsResponseAppleS2SNotifications | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            app_id=app_id,
        )
    ).parsed
