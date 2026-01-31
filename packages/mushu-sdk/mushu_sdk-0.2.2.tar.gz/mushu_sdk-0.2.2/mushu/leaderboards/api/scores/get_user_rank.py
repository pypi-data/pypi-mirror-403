from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.rank_response import RankResponse
from ...models.time_window import TimeWindow
from ...types import UNSET, Response, Unset


def _get_kwargs(
    app_id: str,
    board_id: str,
    user_id: str,
    *,
    time_window: TimeWindow | Unset = UNSET,
    x_api_key: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-key"] = x_api_key

    params: dict[str, Any] = {}

    json_time_window: str | Unset = UNSET
    if not isinstance(time_window, Unset):
        json_time_window = time_window.value

    params["time_window"] = json_time_window

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/apps/{app_id}/boards/{board_id}/rank/{user_id}".format(
            app_id=quote(str(app_id), safe=""),
            board_id=quote(str(board_id), safe=""),
            user_id=quote(str(user_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | RankResponse | None:
    if response.status_code == 200:
        response_200 = RankResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | RankResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    app_id: str,
    board_id: str,
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
    time_window: TimeWindow | Unset = UNSET,
    x_api_key: str,
) -> Response[HTTPValidationError | RankResponse]:
    """Get User Rank

     Get a user's rank on the leaderboard.

    Args:
        app_id (str):
        board_id (str):
        user_id (str):
        time_window (TimeWindow | Unset): Time window for leaderboard aggregation.
        x_api_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RankResponse]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        board_id=board_id,
        user_id=user_id,
        time_window=time_window,
        x_api_key=x_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    app_id: str,
    board_id: str,
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
    time_window: TimeWindow | Unset = UNSET,
    x_api_key: str,
) -> HTTPValidationError | RankResponse | None:
    """Get User Rank

     Get a user's rank on the leaderboard.

    Args:
        app_id (str):
        board_id (str):
        user_id (str):
        time_window (TimeWindow | Unset): Time window for leaderboard aggregation.
        x_api_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RankResponse
    """

    return sync_detailed(
        app_id=app_id,
        board_id=board_id,
        user_id=user_id,
        client=client,
        time_window=time_window,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    app_id: str,
    board_id: str,
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
    time_window: TimeWindow | Unset = UNSET,
    x_api_key: str,
) -> Response[HTTPValidationError | RankResponse]:
    """Get User Rank

     Get a user's rank on the leaderboard.

    Args:
        app_id (str):
        board_id (str):
        user_id (str):
        time_window (TimeWindow | Unset): Time window for leaderboard aggregation.
        x_api_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RankResponse]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        board_id=board_id,
        user_id=user_id,
        time_window=time_window,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    app_id: str,
    board_id: str,
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
    time_window: TimeWindow | Unset = UNSET,
    x_api_key: str,
) -> HTTPValidationError | RankResponse | None:
    """Get User Rank

     Get a user's rank on the leaderboard.

    Args:
        app_id (str):
        board_id (str):
        user_id (str):
        time_window (TimeWindow | Unset): Time window for leaderboard aggregation.
        x_api_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RankResponse
    """

    return (
        await asyncio_detailed(
            app_id=app_id,
            board_id=board_id,
            user_id=user_id,
            client=client,
            time_window=time_window,
            x_api_key=x_api_key,
        )
    ).parsed
