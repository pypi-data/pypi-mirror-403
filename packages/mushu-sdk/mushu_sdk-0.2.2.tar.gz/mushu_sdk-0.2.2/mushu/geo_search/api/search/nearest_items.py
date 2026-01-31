from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.nearest_request import NearestRequest
from ...models.search_response import SearchResponse
from ...types import Response


def _get_kwargs(
    collection: str,
    *,
    body: NearestRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/{collection}/nearest".format(
            collection=quote(str(collection), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | SearchResponse | None:
    if response.status_code == 200:
        response_200 = SearchResponse.from_dict(response.json())

        return response_200

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
) -> Response[ErrorResponse | SearchResponse]:
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
    body: NearestRequest,
) -> Response[ErrorResponse | SearchResponse]:
    """
    Args:
        collection (str): Collection name (e.g., groups, events, places) Example: groups.
        body (NearestRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | SearchResponse]
    """

    kwargs = _get_kwargs(
        collection=collection,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    collection: str,
    *,
    client: AuthenticatedClient,
    body: NearestRequest,
) -> ErrorResponse | SearchResponse | None:
    """
    Args:
        collection (str): Collection name (e.g., groups, events, places) Example: groups.
        body (NearestRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | SearchResponse
    """

    return sync_detailed(
        collection=collection,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    collection: str,
    *,
    client: AuthenticatedClient,
    body: NearestRequest,
) -> Response[ErrorResponse | SearchResponse]:
    """
    Args:
        collection (str): Collection name (e.g., groups, events, places) Example: groups.
        body (NearestRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | SearchResponse]
    """

    kwargs = _get_kwargs(
        collection=collection,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    collection: str,
    *,
    client: AuthenticatedClient,
    body: NearestRequest,
) -> ErrorResponse | SearchResponse | None:
    """
    Args:
        collection (str): Collection name (e.g., groups, events, places) Example: groups.
        body (NearestRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | SearchResponse
    """

    return (
        await asyncio_detailed(
            collection=collection,
            client=client,
            body=body,
        )
    ).parsed
