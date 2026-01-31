from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.put_item_request import PutItemRequest
from ...models.put_item_response import PutItemResponse
from ...types import Response


def _get_kwargs(
    collection: str,
    id: str,
    *,
    body: PutItemRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/{collection}/{id}".format(
            collection=quote(str(collection), safe=""),
            id=quote(str(id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | PutItemResponse | None:
    if response.status_code == 201:
        response_201 = PutItemResponse.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = ErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorResponse | PutItemResponse]:
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
    body: PutItemRequest,
) -> Response[ErrorResponse | PutItemResponse]:
    """
    Args:
        collection (str): Collection name (e.g., groups, events, places) Example: groups.
        id (str): Unique item identifier Example: item-123.
        body (PutItemRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | PutItemResponse]
    """

    kwargs = _get_kwargs(
        collection=collection,
        id=id,
        body=body,
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
    body: PutItemRequest,
) -> ErrorResponse | PutItemResponse | None:
    """
    Args:
        collection (str): Collection name (e.g., groups, events, places) Example: groups.
        id (str): Unique item identifier Example: item-123.
        body (PutItemRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | PutItemResponse
    """

    return sync_detailed(
        collection=collection,
        id=id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    collection: str,
    id: str,
    *,
    client: AuthenticatedClient,
    body: PutItemRequest,
) -> Response[ErrorResponse | PutItemResponse]:
    """
    Args:
        collection (str): Collection name (e.g., groups, events, places) Example: groups.
        id (str): Unique item identifier Example: item-123.
        body (PutItemRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | PutItemResponse]
    """

    kwargs = _get_kwargs(
        collection=collection,
        id=id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    collection: str,
    id: str,
    *,
    client: AuthenticatedClient,
    body: PutItemRequest,
) -> ErrorResponse | PutItemResponse | None:
    """
    Args:
        collection (str): Collection name (e.g., groups, events, places) Example: groups.
        id (str): Unique item identifier Example: item-123.
        body (PutItemRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | PutItemResponse
    """

    return (
        await asyncio_detailed(
            collection=collection,
            id=id,
            client=client,
            body=body,
        )
    ).parsed
