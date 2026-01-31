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
    org_id: str,
    *,
    limit: int | Unset = 100,
    authorization: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["authorization"] = authorization

    params: dict[str, Any] = {}

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/media/org/{org_id}".format(
            org_id=quote(str(org_id), safe=""),
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
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 100,
    authorization: str,
) -> Response[HTTPValidationError | MediaListResponse]:
    """List Org Media

     List all media items for an organization.

    Args:
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
        org_id=org_id,
        limit=limit,
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
    limit: int | Unset = 100,
    authorization: str,
) -> HTTPValidationError | MediaListResponse | None:
    """List Org Media

     List all media items for an organization.

    Args:
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
        org_id=org_id,
        client=client,
        limit=limit,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 100,
    authorization: str,
) -> Response[HTTPValidationError | MediaListResponse]:
    """List Org Media

     List all media items for an organization.

    Args:
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
        org_id=org_id,
        limit=limit,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    org_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 100,
    authorization: str,
) -> HTTPValidationError | MediaListResponse | None:
    """List Org Media

     List all media items for an organization.

    Args:
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
            org_id=org_id,
            client=client,
            limit=limit,
            authorization=authorization,
        )
    ).parsed
