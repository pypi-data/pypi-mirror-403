from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.submit_score_request import SubmitScoreRequest
from ...models.submit_score_response import SubmitScoreResponse
from ...types import Response


def _get_kwargs(
    app_id: str,
    board_id: str,
    *,
    body: SubmitScoreRequest,
    x_api_key: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-key"] = x_api_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/apps/{app_id}/boards/{board_id}/scores".format(
            app_id=quote(str(app_id), safe=""),
            board_id=quote(str(board_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | SubmitScoreResponse | None:
    if response.status_code == 200:
        response_200 = SubmitScoreResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | SubmitScoreResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    app_id: str,
    board_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SubmitScoreRequest,
    x_api_key: str,
) -> Response[HTTPValidationError | SubmitScoreResponse]:
    """Submit Score

     Submit a score to the leaderboard.

    Args:
        app_id (str):
        board_id (str):
        x_api_key (str):
        body (SubmitScoreRequest): Request to submit a score.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SubmitScoreResponse]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        board_id=board_id,
        body=body,
        x_api_key=x_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    app_id: str,
    board_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SubmitScoreRequest,
    x_api_key: str,
) -> HTTPValidationError | SubmitScoreResponse | None:
    """Submit Score

     Submit a score to the leaderboard.

    Args:
        app_id (str):
        board_id (str):
        x_api_key (str):
        body (SubmitScoreRequest): Request to submit a score.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SubmitScoreResponse
    """

    return sync_detailed(
        app_id=app_id,
        board_id=board_id,
        client=client,
        body=body,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    app_id: str,
    board_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SubmitScoreRequest,
    x_api_key: str,
) -> Response[HTTPValidationError | SubmitScoreResponse]:
    """Submit Score

     Submit a score to the leaderboard.

    Args:
        app_id (str):
        board_id (str):
        x_api_key (str):
        body (SubmitScoreRequest): Request to submit a score.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SubmitScoreResponse]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        board_id=board_id,
        body=body,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    app_id: str,
    board_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SubmitScoreRequest,
    x_api_key: str,
) -> HTTPValidationError | SubmitScoreResponse | None:
    """Submit Score

     Submit a score to the leaderboard.

    Args:
        app_id (str):
        board_id (str):
        x_api_key (str):
        body (SubmitScoreRequest): Request to submit a score.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SubmitScoreResponse
    """

    return (
        await asyncio_detailed(
            app_id=app_id,
            board_id=board_id,
            client=client,
            body=body,
            x_api_key=x_api_key,
        )
    ).parsed
