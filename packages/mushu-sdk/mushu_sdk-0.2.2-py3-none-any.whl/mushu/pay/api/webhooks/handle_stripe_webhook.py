from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.handle_stripe_webhook_response_handle_stripe_webhook import (
    HandleStripeWebhookResponseHandleStripeWebhook,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    org_id: str,
    *,
    stripe_signature: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["Stripe-Signature"] = stripe_signature

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/orgs/{org_id}/webhooks/stripe".format(
            org_id=quote(str(org_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | HandleStripeWebhookResponseHandleStripeWebhook | None:
    if response.status_code == 200:
        response_200 = HandleStripeWebhookResponseHandleStripeWebhook.from_dict(response.json())

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
) -> Response[HTTPValidationError | HandleStripeWebhookResponseHandleStripeWebhook]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    stripe_signature: str,
) -> Response[HTTPValidationError | HandleStripeWebhookResponseHandleStripeWebhook]:
    """Handle Stripe Webhook

     Handle Stripe webhook events.

    Args:
        org_id (str):
        stripe_signature (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | HandleStripeWebhookResponseHandleStripeWebhook]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        stripe_signature=stripe_signature,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    stripe_signature: str,
) -> HTTPValidationError | HandleStripeWebhookResponseHandleStripeWebhook | None:
    """Handle Stripe Webhook

     Handle Stripe webhook events.

    Args:
        org_id (str):
        stripe_signature (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | HandleStripeWebhookResponseHandleStripeWebhook
    """

    return sync_detailed(
        org_id=org_id,
        client=client,
        stripe_signature=stripe_signature,
    ).parsed


async def asyncio_detailed(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    stripe_signature: str,
) -> Response[HTTPValidationError | HandleStripeWebhookResponseHandleStripeWebhook]:
    """Handle Stripe Webhook

     Handle Stripe webhook events.

    Args:
        org_id (str):
        stripe_signature (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | HandleStripeWebhookResponseHandleStripeWebhook]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        stripe_signature=stripe_signature,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    stripe_signature: str,
) -> HTTPValidationError | HandleStripeWebhookResponseHandleStripeWebhook | None:
    """Handle Stripe Webhook

     Handle Stripe webhook events.

    Args:
        org_id (str):
        stripe_signature (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | HandleStripeWebhookResponseHandleStripeWebhook
    """

    return (
        await asyncio_detailed(
            org_id=org_id,
            client=client,
            stripe_signature=stripe_signature,
        )
    ).parsed
