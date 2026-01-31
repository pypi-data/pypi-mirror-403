from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.video_upload_url_request import VideoUploadUrlRequest
from ...models.video_upload_url_response import VideoUploadUrlResponse
from ...types import Response


def _get_kwargs(
    *,
    body: VideoUploadUrlRequest,
    authorization: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["authorization"] = authorization

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/media/video/upload-url",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | VideoUploadUrlResponse | None:
    if response.status_code == 200:
        response_200 = VideoUploadUrlResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | VideoUploadUrlResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: VideoUploadUrlRequest,
    authorization: str,
) -> Response[HTTPValidationError | VideoUploadUrlResponse]:
    """Get Video Upload Url

     Generate a presigned URL for video upload to R2.

    Upload flow:
    1. Call this endpoint to get upload URL
    2. Upload video directly to R2 using the presigned URL
    3. Call POST /media/{media_id}/confirm to start transcoding
    4. Poll GET /media/{media_id}/video to check processing status

    After processing completes, the following variants are available:
    - original: The uploaded video
    - optimized: H.264 MP4 (1080p max, 8Mbps) for universal playback
    - web: VP9 WebM (1080p max, 5Mbps) for smaller downloads
    - thumbnail: JPEG thumbnail (640x360)
    - poster: JPEG poster image (1280x720)

    Args:
        authorization (str):
        body (VideoUploadUrlRequest): Request for video upload URL.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | VideoUploadUrlResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: VideoUploadUrlRequest,
    authorization: str,
) -> HTTPValidationError | VideoUploadUrlResponse | None:
    """Get Video Upload Url

     Generate a presigned URL for video upload to R2.

    Upload flow:
    1. Call this endpoint to get upload URL
    2. Upload video directly to R2 using the presigned URL
    3. Call POST /media/{media_id}/confirm to start transcoding
    4. Poll GET /media/{media_id}/video to check processing status

    After processing completes, the following variants are available:
    - original: The uploaded video
    - optimized: H.264 MP4 (1080p max, 8Mbps) for universal playback
    - web: VP9 WebM (1080p max, 5Mbps) for smaller downloads
    - thumbnail: JPEG thumbnail (640x360)
    - poster: JPEG poster image (1280x720)

    Args:
        authorization (str):
        body (VideoUploadUrlRequest): Request for video upload URL.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | VideoUploadUrlResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: VideoUploadUrlRequest,
    authorization: str,
) -> Response[HTTPValidationError | VideoUploadUrlResponse]:
    """Get Video Upload Url

     Generate a presigned URL for video upload to R2.

    Upload flow:
    1. Call this endpoint to get upload URL
    2. Upload video directly to R2 using the presigned URL
    3. Call POST /media/{media_id}/confirm to start transcoding
    4. Poll GET /media/{media_id}/video to check processing status

    After processing completes, the following variants are available:
    - original: The uploaded video
    - optimized: H.264 MP4 (1080p max, 8Mbps) for universal playback
    - web: VP9 WebM (1080p max, 5Mbps) for smaller downloads
    - thumbnail: JPEG thumbnail (640x360)
    - poster: JPEG poster image (1280x720)

    Args:
        authorization (str):
        body (VideoUploadUrlRequest): Request for video upload URL.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | VideoUploadUrlResponse]
    """

    kwargs = _get_kwargs(
        body=body,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: VideoUploadUrlRequest,
    authorization: str,
) -> HTTPValidationError | VideoUploadUrlResponse | None:
    """Get Video Upload Url

     Generate a presigned URL for video upload to R2.

    Upload flow:
    1. Call this endpoint to get upload URL
    2. Upload video directly to R2 using the presigned URL
    3. Call POST /media/{media_id}/confirm to start transcoding
    4. Poll GET /media/{media_id}/video to check processing status

    After processing completes, the following variants are available:
    - original: The uploaded video
    - optimized: H.264 MP4 (1080p max, 8Mbps) for universal playback
    - web: VP9 WebM (1080p max, 5Mbps) for smaller downloads
    - thumbnail: JPEG thumbnail (640x360)
    - poster: JPEG poster image (1280x720)

    Args:
        authorization (str):
        body (VideoUploadUrlRequest): Request for video upload URL.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | VideoUploadUrlResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            authorization=authorization,
        )
    ).parsed
