from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.transaction_list_response import TransactionListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    org_id: str,
    *,
    limit: int | Unset = 50,
    x_api_key: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-key"] = x_api_key

    params: dict[str, Any] = {}

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/orgs/{org_id}/wallet/transactions".format(
            org_id=quote(str(org_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TransactionListResponse | None:
    if response.status_code == 200:
        response_200 = TransactionListResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | TransactionListResponse]:
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
    limit: int | Unset = 50,
    x_api_key: str,
) -> Response[HTTPValidationError | TransactionListResponse]:
    """List Transactions

     List wallet transactions for the organization.

    Args:
        org_id (str):
        limit (int | Unset):  Default: 50.
        x_api_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TransactionListResponse]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        limit=limit,
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
    limit: int | Unset = 50,
    x_api_key: str,
) -> HTTPValidationError | TransactionListResponse | None:
    """List Transactions

     List wallet transactions for the organization.

    Args:
        org_id (str):
        limit (int | Unset):  Default: 50.
        x_api_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TransactionListResponse
    """

    return sync_detailed(
        org_id=org_id,
        client=client,
        limit=limit,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    x_api_key: str,
) -> Response[HTTPValidationError | TransactionListResponse]:
    """List Transactions

     List wallet transactions for the organization.

    Args:
        org_id (str):
        limit (int | Unset):  Default: 50.
        x_api_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TransactionListResponse]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        limit=limit,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    x_api_key: str,
) -> HTTPValidationError | TransactionListResponse | None:
    """List Transactions

     List wallet transactions for the organization.

    Args:
        org_id (str):
        limit (int | Unset):  Default: 50.
        x_api_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TransactionListResponse
    """

    return (
        await asyncio_detailed(
            org_id=org_id,
            client=client,
            limit=limit,
            x_api_key=x_api_key,
        )
    ).parsed
