from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_webhook_endpoint_request import CreateWebhookEndpointRequest
from ...models.http_validation_error import HTTPValidationError
from ...models.webhook_endpoint import WebhookEndpoint
from ...types import Response


def _get_kwargs(
    app_id: str,
    *,
    body: CreateWebhookEndpointRequest,
    authorization: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["authorization"] = authorization

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/apps/{app_id}/webhooks".format(
            app_id=quote(str(app_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | WebhookEndpoint | None:
    if response.status_code == 200:
        response_200 = WebhookEndpoint.from_dict(response.json())

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
) -> Response[HTTPValidationError | WebhookEndpoint]:
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
    body: CreateWebhookEndpointRequest,
    authorization: str,
) -> Response[HTTPValidationError | WebhookEndpoint]:
    """Create Webhook Endpoint

     Create a webhook endpoint. Requires admin role in org.
    The signing secret is only returned on creation - store it securely.

    Args:
        app_id (str):
        authorization (str):
        body (CreateWebhookEndpointRequest): Request to create a webhook endpoint.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | WebhookEndpoint]
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
    body: CreateWebhookEndpointRequest,
    authorization: str,
) -> HTTPValidationError | WebhookEndpoint | None:
    """Create Webhook Endpoint

     Create a webhook endpoint. Requires admin role in org.
    The signing secret is only returned on creation - store it securely.

    Args:
        app_id (str):
        authorization (str):
        body (CreateWebhookEndpointRequest): Request to create a webhook endpoint.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | WebhookEndpoint
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
    body: CreateWebhookEndpointRequest,
    authorization: str,
) -> Response[HTTPValidationError | WebhookEndpoint]:
    """Create Webhook Endpoint

     Create a webhook endpoint. Requires admin role in org.
    The signing secret is only returned on creation - store it securely.

    Args:
        app_id (str):
        authorization (str):
        body (CreateWebhookEndpointRequest): Request to create a webhook endpoint.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | WebhookEndpoint]
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
    body: CreateWebhookEndpointRequest,
    authorization: str,
) -> HTTPValidationError | WebhookEndpoint | None:
    """Create Webhook Endpoint

     Create a webhook endpoint. Requires admin role in org.
    The signing secret is only returned on creation - store it securely.

    Args:
        app_id (str):
        authorization (str):
        body (CreateWebhookEndpointRequest): Request to create a webhook endpoint.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | WebhookEndpoint
    """

    return (
        await asyncio_detailed(
            app_id=app_id,
            client=client,
            body=body,
            authorization=authorization,
        )
    ).parsed
