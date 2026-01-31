from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.media_list_response import MediaListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    app_id: str,
    *,
    org_id: str,
    limit: int | Unset = 100,
    authorization: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["authorization"] = authorization

    params: dict[str, Any] = {}

    params["org_id"] = org_id

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/media/app/{app_id}".format(
            app_id=quote(str(app_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | MediaListResponse | None:
    if response.status_code == 200:
        response_200 = MediaListResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | MediaListResponse]:
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
    org_id: str,
    limit: int | Unset = 100,
    authorization: str,
) -> Response[HTTPValidationError | MediaListResponse]:
    """List App Media

     List all media items for an app.

    Args:
        app_id (str):
        org_id (str):
        limit (int | Unset):  Default: 100.
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MediaListResponse]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        org_id=org_id,
        limit=limit,
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
    org_id: str,
    limit: int | Unset = 100,
    authorization: str,
) -> HTTPValidationError | MediaListResponse | None:
    """List App Media

     List all media items for an app.

    Args:
        app_id (str):
        org_id (str):
        limit (int | Unset):  Default: 100.
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MediaListResponse
    """

    return sync_detailed(
        app_id=app_id,
        client=client,
        org_id=org_id,
        limit=limit,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    app_id: str,
    *,
    client: AuthenticatedClient | Client,
    org_id: str,
    limit: int | Unset = 100,
    authorization: str,
) -> Response[HTTPValidationError | MediaListResponse]:
    """List App Media

     List all media items for an app.

    Args:
        app_id (str):
        org_id (str):
        limit (int | Unset):  Default: 100.
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | MediaListResponse]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        org_id=org_id,
        limit=limit,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    app_id: str,
    *,
    client: AuthenticatedClient | Client,
    org_id: str,
    limit: int | Unset = 100,
    authorization: str,
) -> HTTPValidationError | MediaListResponse | None:
    """List App Media

     List all media items for an app.

    Args:
        app_id (str):
        org_id (str):
        limit (int | Unset):  Default: 100.
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | MediaListResponse
    """

    return (
        await asyncio_detailed(
            app_id=app_id,
            client=client,
            org_id=org_id,
            limit=limit,
            authorization=authorization,
        )
    ).parsed
