from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.streak import Streak
from ...types import UNSET, Response, Unset


def _get_kwargs(
    app_id: str,
    user_id: str,
    *,
    activity_type: None | str | Unset = UNSET,
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

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/apps/{app_id}/streaks/{user_id}".format(
            app_id=quote(str(app_id), safe=""),
            user_id=quote(str(user_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list[Streak] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = Streak.from_dict(response_200_item_data)

            response_200.append(response_200_item)

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
) -> Response[HTTPValidationError | list[Streak]]:
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
    x_api_key: str,
) -> Response[HTTPValidationError | list[Streak]]:
    """Get User Streaks

     Get user's streak information.

    Args:
        app_id (str):
        user_id (str):
        activity_type (None | str | Unset): Filter by activity type
        x_api_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[Streak]]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        user_id=user_id,
        activity_type=activity_type,
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
    x_api_key: str,
) -> HTTPValidationError | list[Streak] | None:
    """Get User Streaks

     Get user's streak information.

    Args:
        app_id (str):
        user_id (str):
        activity_type (None | str | Unset): Filter by activity type
        x_api_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[Streak]
    """

    return sync_detailed(
        app_id=app_id,
        user_id=user_id,
        client=client,
        activity_type=activity_type,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    app_id: str,
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
    activity_type: None | str | Unset = UNSET,
    x_api_key: str,
) -> Response[HTTPValidationError | list[Streak]]:
    """Get User Streaks

     Get user's streak information.

    Args:
        app_id (str):
        user_id (str):
        activity_type (None | str | Unset): Filter by activity type
        x_api_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[Streak]]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        user_id=user_id,
        activity_type=activity_type,
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
    x_api_key: str,
) -> HTTPValidationError | list[Streak] | None:
    """Get User Streaks

     Get user's streak information.

    Args:
        app_id (str):
        user_id (str):
        activity_type (None | str | Unset): Filter by activity type
        x_api_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[Streak]
    """

    return (
        await asyncio_detailed(
            app_id=app_id,
            user_id=user_id,
            client=client,
            activity_type=activity_type,
            x_api_key=x_api_key,
        )
    ).parsed
