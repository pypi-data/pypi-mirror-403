from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.record_activity_request import RecordActivityRequest
from ...models.record_activity_response import RecordActivityResponse
from ...types import Response


def _get_kwargs(
    app_id: str,
    user_id: str,
    *,
    body: RecordActivityRequest,
    x_api_key: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-key"] = x_api_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/apps/{app_id}/streaks/{user_id}/record".format(
            app_id=quote(str(app_id), safe=""),
            user_id=quote(str(user_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | RecordActivityResponse | None:
    if response.status_code == 200:
        response_200 = RecordActivityResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | RecordActivityResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    app_id: str,
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: RecordActivityRequest,
    x_api_key: str,
) -> Response[HTTPValidationError | RecordActivityResponse]:
    """Record Activity

     Record an activity and update streak.

    Args:
        app_id (str):
        user_id (str):
        x_api_key (str):
        body (RecordActivityRequest): Request to record an activity.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RecordActivityResponse]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        user_id=user_id,
        body=body,
        x_api_key=x_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    app_id: str,
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: RecordActivityRequest,
    x_api_key: str,
) -> HTTPValidationError | RecordActivityResponse | None:
    """Record Activity

     Record an activity and update streak.

    Args:
        app_id (str):
        user_id (str):
        x_api_key (str):
        body (RecordActivityRequest): Request to record an activity.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RecordActivityResponse
    """

    return sync_detailed(
        app_id=app_id,
        user_id=user_id,
        client=client,
        body=body,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    app_id: str,
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: RecordActivityRequest,
    x_api_key: str,
) -> Response[HTTPValidationError | RecordActivityResponse]:
    """Record Activity

     Record an activity and update streak.

    Args:
        app_id (str):
        user_id (str):
        x_api_key (str):
        body (RecordActivityRequest): Request to record an activity.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RecordActivityResponse]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        user_id=user_id,
        body=body,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    app_id: str,
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: RecordActivityRequest,
    x_api_key: str,
) -> HTTPValidationError | RecordActivityResponse | None:
    """Record Activity

     Record an activity and update streak.

    Args:
        app_id (str):
        user_id (str):
        x_api_key (str):
        body (RecordActivityRequest): Request to record an activity.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RecordActivityResponse
    """

    return (
        await asyncio_detailed(
            app_id=app_id,
            user_id=user_id,
            client=client,
            body=body,
            x_api_key=x_api_key,
        )
    ).parsed
