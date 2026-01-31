from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.http_validation_error import HTTPValidationError
from ...models.upload_url_request import UploadUrlRequest
from ...models.upload_url_response import UploadUrlResponse
from ...types import Response


def _get_kwargs(
    *,
    body: UploadUrlRequest,
    authorization: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["authorization"] = authorization

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/media/upload-url",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | HTTPValidationError | UploadUrlResponse | None:
    if response.status_code == 200:
        response_200 = UploadUrlResponse.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = ErrorResponse.from_dict(response.json())

        return response_403

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorResponse | HTTPValidationError | UploadUrlResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: UploadUrlRequest,
    authorization: str,
) -> Response[ErrorResponse | HTTPValidationError | UploadUrlResponse]:
    """Get Upload Url

     Generate a presigned URL for uploading media.

    The URL can be used to upload directly to R2, bypassing the API.
    After upload, call POST /media/{media_id}/confirm to confirm.

    Args:
        authorization (str):
        body (UploadUrlRequest): Request to generate a presigned upload URL.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | HTTPValidationError | UploadUrlResponse]
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
    body: UploadUrlRequest,
    authorization: str,
) -> ErrorResponse | HTTPValidationError | UploadUrlResponse | None:
    """Get Upload Url

     Generate a presigned URL for uploading media.

    The URL can be used to upload directly to R2, bypassing the API.
    After upload, call POST /media/{media_id}/confirm to confirm.

    Args:
        authorization (str):
        body (UploadUrlRequest): Request to generate a presigned upload URL.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | HTTPValidationError | UploadUrlResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: UploadUrlRequest,
    authorization: str,
) -> Response[ErrorResponse | HTTPValidationError | UploadUrlResponse]:
    """Get Upload Url

     Generate a presigned URL for uploading media.

    The URL can be used to upload directly to R2, bypassing the API.
    After upload, call POST /media/{media_id}/confirm to confirm.

    Args:
        authorization (str):
        body (UploadUrlRequest): Request to generate a presigned upload URL.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | HTTPValidationError | UploadUrlResponse]
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
    body: UploadUrlRequest,
    authorization: str,
) -> ErrorResponse | HTTPValidationError | UploadUrlResponse | None:
    """Get Upload Url

     Generate a presigned URL for uploading media.

    The URL can be used to upload directly to R2, bypassing the API.
    After upload, call POST /media/{media_id}/confirm to confirm.

    Args:
        authorization (str):
        body (UploadUrlRequest): Request to generate a presigned upload URL.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | HTTPValidationError | UploadUrlResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            authorization=authorization,
        )
    ).parsed
