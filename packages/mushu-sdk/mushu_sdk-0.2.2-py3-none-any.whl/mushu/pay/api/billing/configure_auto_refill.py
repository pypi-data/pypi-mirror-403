from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.auto_refill_config import AutoRefillConfig
from ...models.http_validation_error import HTTPValidationError
from ...models.org_billing import OrgBilling
from ...types import Response


def _get_kwargs(
    org_id: str,
    *,
    body: AutoRefillConfig,
    authorization: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["authorization"] = authorization

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/orgs/{org_id}/billing/auto-refill".format(
            org_id=quote(str(org_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | OrgBilling | None:
    if response.status_code == 200:
        response_200 = OrgBilling.from_dict(response.json())

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
) -> Response[HTTPValidationError | OrgBilling]:
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
    body: AutoRefillConfig,
    authorization: str,
) -> Response[HTTPValidationError | OrgBilling]:
    """Configure Auto Refill

     Configure auto-refill for an organization.

    Args:
        org_id (str):
        authorization (str):
        body (AutoRefillConfig): Auto-refill configuration.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | OrgBilling]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        body=body,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: AutoRefillConfig,
    authorization: str,
) -> HTTPValidationError | OrgBilling | None:
    """Configure Auto Refill

     Configure auto-refill for an organization.

    Args:
        org_id (str):
        authorization (str):
        body (AutoRefillConfig): Auto-refill configuration.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | OrgBilling
    """

    return sync_detailed(
        org_id=org_id,
        client=client,
        body=body,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: AutoRefillConfig,
    authorization: str,
) -> Response[HTTPValidationError | OrgBilling]:
    """Configure Auto Refill

     Configure auto-refill for an organization.

    Args:
        org_id (str):
        authorization (str):
        body (AutoRefillConfig): Auto-refill configuration.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | OrgBilling]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        body=body,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: AutoRefillConfig,
    authorization: str,
) -> HTTPValidationError | OrgBilling | None:
    """Configure Auto Refill

     Configure auto-refill for an organization.

    Args:
        org_id (str):
        authorization (str):
        body (AutoRefillConfig): Auto-refill configuration.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | OrgBilling
    """

    return (
        await asyncio_detailed(
            org_id=org_id,
            client=client,
            body=body,
            authorization=authorization,
        )
    ).parsed
