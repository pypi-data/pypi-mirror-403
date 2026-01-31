from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.org_billing import OrgBilling
from ...types import Response


def _get_kwargs(
    org_id: str,
    *,
    x_api_key: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-key"] = x_api_key

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/orgs/{org_id}/wallet".format(
            org_id=quote(str(org_id), safe=""),
        ),
    }

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
    x_api_key: str,
) -> Response[HTTPValidationError | OrgBilling]:
    """Get Wallet Balance

     Get the organization's wallet balance and billing info.

    Args:
        org_id (str):
        x_api_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | OrgBilling]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        x_api_key=x_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    x_api_key: str,
) -> HTTPValidationError | OrgBilling | None:
    """Get Wallet Balance

     Get the organization's wallet balance and billing info.

    Args:
        org_id (str):
        x_api_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | OrgBilling
    """

    return sync_detailed(
        org_id=org_id,
        client=client,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    x_api_key: str,
) -> Response[HTTPValidationError | OrgBilling]:
    """Get Wallet Balance

     Get the organization's wallet balance and billing info.

    Args:
        org_id (str):
        x_api_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | OrgBilling]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    x_api_key: str,
) -> HTTPValidationError | OrgBilling | None:
    """Get Wallet Balance

     Get the organization's wallet balance and billing info.

    Args:
        org_id (str):
        x_api_key (str):

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
            x_api_key=x_api_key,
        )
    ).parsed
