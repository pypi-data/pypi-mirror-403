from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.confirm_upload_response import ConfirmUploadResponse
from ...models.error_response import ErrorResponse
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
        "method": "post",
        "url": "/media/{media_id}/confirm".format(
            media_id=quote(str(media_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ConfirmUploadResponse | ErrorResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = ConfirmUploadResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = ErrorResponse.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = ErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ConfirmUploadResponse | ErrorResponse | HTTPValidationError]:
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
) -> Response[ConfirmUploadResponse | ErrorResponse | HTTPValidationError]:
    """Confirm Upload

     Confirm that a media upload is complete.

    For images/documents: Verifies file exists in R2 and marks as READY.
    For videos: Copies to S3 staging and starts MediaConvert transcoding.

    Args:
        media_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ConfirmUploadResponse | ErrorResponse | HTTPValidationError]
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
) -> ConfirmUploadResponse | ErrorResponse | HTTPValidationError | None:
    """Confirm Upload

     Confirm that a media upload is complete.

    For images/documents: Verifies file exists in R2 and marks as READY.
    For videos: Copies to S3 staging and starts MediaConvert transcoding.

    Args:
        media_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ConfirmUploadResponse | ErrorResponse | HTTPValidationError
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
) -> Response[ConfirmUploadResponse | ErrorResponse | HTTPValidationError]:
    """Confirm Upload

     Confirm that a media upload is complete.

    For images/documents: Verifies file exists in R2 and marks as READY.
    For videos: Copies to S3 staging and starts MediaConvert transcoding.

    Args:
        media_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ConfirmUploadResponse | ErrorResponse | HTTPValidationError]
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
) -> ConfirmUploadResponse | ErrorResponse | HTTPValidationError | None:
    """Confirm Upload

     Confirm that a media upload is complete.

    For images/documents: Verifies file exists in R2 and marks as READY.
    For videos: Copies to S3 staging and starts MediaConvert transcoding.

    Args:
        media_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ConfirmUploadResponse | ErrorResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            media_id=media_id,
            client=client,
            authorization=authorization,
        )
    ).parsed
