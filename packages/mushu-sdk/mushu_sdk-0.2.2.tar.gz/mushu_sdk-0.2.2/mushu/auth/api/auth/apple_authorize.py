from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    redirect_uri: str,
    client_id: None | str | Unset = UNSET,
    app_id: None | str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["redirect_uri"] = redirect_uri

    json_client_id: None | str | Unset
    if isinstance(client_id, Unset):
        json_client_id = UNSET
    else:
        json_client_id = client_id
    params["client_id"] = json_client_id

    json_app_id: None | str | Unset
    if isinstance(app_id, Unset):
        json_app_id = UNSET
    else:
        json_app_id = app_id
    params["app_id"] = json_app_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/auth/apple/authorize",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = response.json()
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
) -> Response[Any | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    redirect_uri: str,
    client_id: None | str | Unset = UNSET,
    app_id: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """Apple Authorize

     Start Apple OAuth web flow.

    Creates OAuth state in DynamoDB and redirects to Apple's authorization URL.
    After user authenticates, Apple will POST to /auth/apple/callback.

    If app_id is provided, the app's Apple credentials will be used (if configured).
    Otherwise, the platform credentials are used.

    Args:
        redirect_uri (str): Final redirect URI for tokens
        client_id (None | str | Unset): Apple Services ID (defaults to config)
        app_id (None | str | Unset): App ID for multi-tenant OAuth

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        redirect_uri=redirect_uri,
        client_id=client_id,
        app_id=app_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    redirect_uri: str,
    client_id: None | str | Unset = UNSET,
    app_id: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """Apple Authorize

     Start Apple OAuth web flow.

    Creates OAuth state in DynamoDB and redirects to Apple's authorization URL.
    After user authenticates, Apple will POST to /auth/apple/callback.

    If app_id is provided, the app's Apple credentials will be used (if configured).
    Otherwise, the platform credentials are used.

    Args:
        redirect_uri (str): Final redirect URI for tokens
        client_id (None | str | Unset): Apple Services ID (defaults to config)
        app_id (None | str | Unset): App ID for multi-tenant OAuth

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        redirect_uri=redirect_uri,
        client_id=client_id,
        app_id=app_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    redirect_uri: str,
    client_id: None | str | Unset = UNSET,
    app_id: None | str | Unset = UNSET,
) -> Response[Any | HTTPValidationError]:
    """Apple Authorize

     Start Apple OAuth web flow.

    Creates OAuth state in DynamoDB and redirects to Apple's authorization URL.
    After user authenticates, Apple will POST to /auth/apple/callback.

    If app_id is provided, the app's Apple credentials will be used (if configured).
    Otherwise, the platform credentials are used.

    Args:
        redirect_uri (str): Final redirect URI for tokens
        client_id (None | str | Unset): Apple Services ID (defaults to config)
        app_id (None | str | Unset): App ID for multi-tenant OAuth

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        redirect_uri=redirect_uri,
        client_id=client_id,
        app_id=app_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    redirect_uri: str,
    client_id: None | str | Unset = UNSET,
    app_id: None | str | Unset = UNSET,
) -> Any | HTTPValidationError | None:
    """Apple Authorize

     Start Apple OAuth web flow.

    Creates OAuth state in DynamoDB and redirects to Apple's authorization URL.
    After user authenticates, Apple will POST to /auth/apple/callback.

    If app_id is provided, the app's Apple credentials will be used (if configured).
    Otherwise, the platform credentials are used.

    Args:
        redirect_uri (str): Final redirect URI for tokens
        client_id (None | str | Unset): Apple Services ID (defaults to config)
        app_id (None | str | Unset): App ID for multi-tenant OAuth

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            redirect_uri=redirect_uri,
            client_id=client_id,
            app_id=app_id,
        )
    ).parsed
