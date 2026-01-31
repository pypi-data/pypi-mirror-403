from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.image_urls_response import ImageUrlsResponse
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
        "url": "/media/{media_id}/images".format(
            media_id=quote(str(media_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | ImageUrlsResponse | None:
    if response.status_code == 200:
        response_200 = ImageUrlsResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | ImageUrlsResponse]:
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
) -> Response[HTTPValidationError | ImageUrlsResponse]:
    """Get Image Urls

     Get image variant URLs for transforms.

    Returns URLs for all available image variants (thumbnail, small, medium, large).
    These URLs point to the Cloudflare Images Worker which performs on-the-fly transforms.

    Only works for image media types.

    Args:
        media_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ImageUrlsResponse]
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
) -> HTTPValidationError | ImageUrlsResponse | None:
    """Get Image Urls

     Get image variant URLs for transforms.

    Returns URLs for all available image variants (thumbnail, small, medium, large).
    These URLs point to the Cloudflare Images Worker which performs on-the-fly transforms.

    Only works for image media types.

    Args:
        media_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ImageUrlsResponse
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
) -> Response[HTTPValidationError | ImageUrlsResponse]:
    """Get Image Urls

     Get image variant URLs for transforms.

    Returns URLs for all available image variants (thumbnail, small, medium, large).
    These URLs point to the Cloudflare Images Worker which performs on-the-fly transforms.

    Only works for image media types.

    Args:
        media_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | ImageUrlsResponse]
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
) -> HTTPValidationError | ImageUrlsResponse | None:
    """Get Image Urls

     Get image variant URLs for transforms.

    Returns URLs for all available image variants (thumbnail, small, medium, large).
    These URLs point to the Cloudflare Images Worker which performs on-the-fly transforms.

    Only works for image media types.

    Args:
        media_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | ImageUrlsResponse
    """

    return (
        await asyncio_detailed(
            media_id=media_id,
            client=client,
            authorization=authorization,
        )
    ).parsed
