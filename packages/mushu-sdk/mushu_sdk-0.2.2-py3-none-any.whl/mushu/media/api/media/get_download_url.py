from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_download_url_response_get_download_url import (
    GetDownloadUrlResponseGetDownloadUrl,
)
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
        "method": "get",
        "url": "/media/{media_id}/url".format(
            media_id=quote(str(media_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GetDownloadUrlResponseGetDownloadUrl | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = GetDownloadUrlResponseGetDownloadUrl.from_dict(response.json())

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
) -> Response[GetDownloadUrlResponseGetDownloadUrl | HTTPValidationError]:
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
) -> Response[GetDownloadUrlResponseGetDownloadUrl | HTTPValidationError]:
    """Get Download Url

     Get a presigned download URL for the media.

    Args:
        media_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetDownloadUrlResponseGetDownloadUrl | HTTPValidationError]
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
) -> GetDownloadUrlResponseGetDownloadUrl | HTTPValidationError | None:
    """Get Download Url

     Get a presigned download URL for the media.

    Args:
        media_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetDownloadUrlResponseGetDownloadUrl | HTTPValidationError
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
) -> Response[GetDownloadUrlResponseGetDownloadUrl | HTTPValidationError]:
    """Get Download Url

     Get a presigned download URL for the media.

    Args:
        media_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetDownloadUrlResponseGetDownloadUrl | HTTPValidationError]
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
) -> GetDownloadUrlResponseGetDownloadUrl | HTTPValidationError | None:
    """Get Download Url

     Get a presigned download URL for the media.

    Args:
        media_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetDownloadUrlResponseGetDownloadUrl | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            media_id=media_id,
            client=client,
            authorization=authorization,
        )
    ).parsed
