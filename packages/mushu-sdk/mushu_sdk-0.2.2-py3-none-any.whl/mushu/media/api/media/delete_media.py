from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_media_response_delete_media import DeleteMediaResponseDeleteMedia
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    media_id: str,
    *,
    authorization: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["authorization"] = authorization

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/media/{media_id}".format(
            media_id=quote(str(media_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DeleteMediaResponseDeleteMedia | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = DeleteMediaResponseDeleteMedia.from_dict(response.json())

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
) -> Response[DeleteMediaResponseDeleteMedia | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    media_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: str,
) -> Response[DeleteMediaResponseDeleteMedia | HTTPValidationError]:
    """Delete Media

     Delete a media item (admin/owner only).

    Args:
        media_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteMediaResponseDeleteMedia | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        media_id=media_id,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    media_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: str,
) -> DeleteMediaResponseDeleteMedia | HTTPValidationError | None:
    """Delete Media

     Delete a media item (admin/owner only).

    Args:
        media_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteMediaResponseDeleteMedia | HTTPValidationError
    """

    return sync_detailed(
        media_id=media_id,
        client=client,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    media_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: str,
) -> Response[DeleteMediaResponseDeleteMedia | HTTPValidationError]:
    """Delete Media

     Delete a media item (admin/owner only).

    Args:
        media_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteMediaResponseDeleteMedia | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        media_id=media_id,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    media_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: str,
) -> DeleteMediaResponseDeleteMedia | HTTPValidationError | None:
    """Delete Media

     Delete a media item (admin/owner only).

    Args:
        media_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteMediaResponseDeleteMedia | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            media_id=media_id,
            client=client,
            authorization=authorization,
        )
    ).parsed
