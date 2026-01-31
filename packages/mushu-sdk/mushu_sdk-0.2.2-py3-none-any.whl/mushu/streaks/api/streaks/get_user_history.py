from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.streak_history import StreakHistory
from ...types import UNSET, Response, Unset


def _get_kwargs(
    app_id: str,
    user_id: str,
    *,
    activity_type: None | str | Unset = UNSET,
    start_date: None | str | Unset = UNSET,
    end_date: None | str | Unset = UNSET,
    limit: int | Unset = 100,
    x_api_key: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-key"] = x_api_key

    params: dict[str, Any] = {}

    json_activity_type: None | str | Unset
    if isinstance(activity_type, Unset):
        json_activity_type = UNSET
    else:
        json_activity_type = activity_type
    params["activity_type"] = json_activity_type

    json_start_date: None | str | Unset
    if isinstance(start_date, Unset):
        json_start_date = UNSET
    else:
        json_start_date = start_date
    params["start_date"] = json_start_date

    json_end_date: None | str | Unset
    if isinstance(end_date, Unset):
        json_end_date = UNSET
    else:
        json_end_date = end_date
    params["end_date"] = json_end_date

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/apps/{app_id}/streaks/{user_id}/history".format(
            app_id=quote(str(app_id), safe=""),
            user_id=quote(str(user_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | StreakHistory | None:
    if response.status_code == 200:
        response_200 = StreakHistory.from_dict(response.json())

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
) -> Response[HTTPValidationError | StreakHistory]:
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
    activity_type: None | str | Unset = UNSET,
    start_date: None | str | Unset = UNSET,
    end_date: None | str | Unset = UNSET,
    limit: int | Unset = 100,
    x_api_key: str,
) -> Response[HTTPValidationError | StreakHistory]:
    """Get User History

     Get user's activity history.

    Args:
        app_id (str):
        user_id (str):
        activity_type (None | str | Unset): Filter by activity type
        start_date (None | str | Unset): Start date (YYYY-MM-DD)
        end_date (None | str | Unset): End date (YYYY-MM-DD)
        limit (int | Unset): Max results Default: 100.
        x_api_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | StreakHistory]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        user_id=user_id,
        activity_type=activity_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
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
    activity_type: None | str | Unset = UNSET,
    start_date: None | str | Unset = UNSET,
    end_date: None | str | Unset = UNSET,
    limit: int | Unset = 100,
    x_api_key: str,
) -> HTTPValidationError | StreakHistory | None:
    """Get User History

     Get user's activity history.

    Args:
        app_id (str):
        user_id (str):
        activity_type (None | str | Unset): Filter by activity type
        start_date (None | str | Unset): Start date (YYYY-MM-DD)
        end_date (None | str | Unset): End date (YYYY-MM-DD)
        limit (int | Unset): Max results Default: 100.
        x_api_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | StreakHistory
    """

    return sync_detailed(
        app_id=app_id,
        user_id=user_id,
        client=client,
        activity_type=activity_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    app_id: str,
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
    activity_type: None | str | Unset = UNSET,
    start_date: None | str | Unset = UNSET,
    end_date: None | str | Unset = UNSET,
    limit: int | Unset = 100,
    x_api_key: str,
) -> Response[HTTPValidationError | StreakHistory]:
    """Get User History

     Get user's activity history.

    Args:
        app_id (str):
        user_id (str):
        activity_type (None | str | Unset): Filter by activity type
        start_date (None | str | Unset): Start date (YYYY-MM-DD)
        end_date (None | str | Unset): End date (YYYY-MM-DD)
        limit (int | Unset): Max results Default: 100.
        x_api_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | StreakHistory]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        user_id=user_id,
        activity_type=activity_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    app_id: str,
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
    activity_type: None | str | Unset = UNSET,
    start_date: None | str | Unset = UNSET,
    end_date: None | str | Unset = UNSET,
    limit: int | Unset = 100,
    x_api_key: str,
) -> HTTPValidationError | StreakHistory | None:
    """Get User History

     Get user's activity history.

    Args:
        app_id (str):
        user_id (str):
        activity_type (None | str | Unset): Filter by activity type
        start_date (None | str | Unset): Start date (YYYY-MM-DD)
        end_date (None | str | Unset): End date (YYYY-MM-DD)
        limit (int | Unset): Max results Default: 100.
        x_api_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | StreakHistory
    """

    return (
        await asyncio_detailed(
            app_id=app_id,
            user_id=user_id,
            client=client,
            activity_type=activity_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            x_api_key=x_api_key,
        )
    ).parsed
