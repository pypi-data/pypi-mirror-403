from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.geo_item import GeoItem
from ...types import Response


def _get_kwargs(
    collection: str,
    id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/{collection}/{id}".format(
            collection=quote(str(collection), safe=""),
            id=quote(str(id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | GeoItem | None:
    if response.status_code == 200:
        response_200 = GeoItem.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 404:
        response_404 = ErrorResponse.from_dict(response.json())

        return response_404

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorResponse | GeoItem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    collection: str,
    id: str,
    *,
    client: AuthenticatedClient,
) -> Response[ErrorResponse | GeoItem]:
    """
    Args:
        collection (str): Collection name (e.g., groups, events, places) Example: groups.
        id (str): Unique item identifier Example: item-123.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | GeoItem]
    """

    kwargs = _get_kwargs(
        collection=collection,
        id=id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    collection: str,
    id: str,
    *,
    client: AuthenticatedClient,
) -> ErrorResponse | GeoItem | None:
    """
    Args:
        collection (str): Collection name (e.g., groups, events, places) Example: groups.
        id (str): Unique item identifier Example: item-123.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | GeoItem
    """

    return sync_detailed(
        collection=collection,
        id=id,
        client=client,
    ).parsed


async def asyncio_detailed(
    collection: str,
    id: str,
    *,
    client: AuthenticatedClient,
) -> Response[ErrorResponse | GeoItem]:
    """
    Args:
        collection (str): Collection name (e.g., groups, events, places) Example: groups.
        id (str): Unique item identifier Example: item-123.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | GeoItem]
    """

    kwargs = _get_kwargs(
        collection=collection,
        id=id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    collection: str,
    id: str,
    *,
    client: AuthenticatedClient,
) -> ErrorResponse | GeoItem | None:
    """
    Args:
        collection (str): Collection name (e.g., groups, events, places) Example: groups.
        id (str): Unique item identifier Example: item-123.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | GeoItem
    """

    return (
        await asyncio_detailed(
            collection=collection,
            id=id,
            client=client,
        )
    ).parsed
