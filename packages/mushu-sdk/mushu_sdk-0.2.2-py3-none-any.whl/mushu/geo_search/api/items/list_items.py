from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.list_response import ListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    collection: str,
    *,
    limit: str | Unset = UNSET,
    cursor: str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["cursor"] = cursor

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/{collection}".format(
            collection=quote(str(collection), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | ListResponse | None:
    if response.status_code == 200:
        response_200 = ListResponse.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorResponse | ListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    collection: str,
    *,
    client: AuthenticatedClient,
    limit: str | Unset = UNSET,
    cursor: str | Unset = UNSET,
) -> Response[ErrorResponse | ListResponse]:
    """
    Args:
        collection (str): Collection name (e.g., groups, events, places) Example: groups.
        limit (str | Unset): Maximum items to return Example: 100.
        cursor (str | Unset): Pagination cursor from previous response Example:
            eyJsYXN0X2lkIjoiYWJjIn0=.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | ListResponse]
    """

    kwargs = _get_kwargs(
        collection=collection,
        limit=limit,
        cursor=cursor,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    collection: str,
    *,
    client: AuthenticatedClient,
    limit: str | Unset = UNSET,
    cursor: str | Unset = UNSET,
) -> ErrorResponse | ListResponse | None:
    """
    Args:
        collection (str): Collection name (e.g., groups, events, places) Example: groups.
        limit (str | Unset): Maximum items to return Example: 100.
        cursor (str | Unset): Pagination cursor from previous response Example:
            eyJsYXN0X2lkIjoiYWJjIn0=.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | ListResponse
    """

    return sync_detailed(
        collection=collection,
        client=client,
        limit=limit,
        cursor=cursor,
    ).parsed


async def asyncio_detailed(
    collection: str,
    *,
    client: AuthenticatedClient,
    limit: str | Unset = UNSET,
    cursor: str | Unset = UNSET,
) -> Response[ErrorResponse | ListResponse]:
    """
    Args:
        collection (str): Collection name (e.g., groups, events, places) Example: groups.
        limit (str | Unset): Maximum items to return Example: 100.
        cursor (str | Unset): Pagination cursor from previous response Example:
            eyJsYXN0X2lkIjoiYWJjIn0=.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | ListResponse]
    """

    kwargs = _get_kwargs(
        collection=collection,
        limit=limit,
        cursor=cursor,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    collection: str,
    *,
    client: AuthenticatedClient,
    limit: str | Unset = UNSET,
    cursor: str | Unset = UNSET,
) -> ErrorResponse | ListResponse | None:
    """
    Args:
        collection (str): Collection name (e.g., groups, events, places) Example: groups.
        limit (str | Unset): Maximum items to return Example: 100.
        cursor (str | Unset): Pagination cursor from previous response Example:
            eyJsYXN0X2lkIjoiYWJjIn0=.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | ListResponse
    """

    return (
        await asyncio_detailed(
            collection=collection,
            client=client,
            limit=limit,
            cursor=cursor,
        )
    ).parsed
