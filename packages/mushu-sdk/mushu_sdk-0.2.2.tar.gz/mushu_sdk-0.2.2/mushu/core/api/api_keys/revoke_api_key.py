from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.revoke_api_key_response_revoke_api_key import RevokeApiKeyResponseRevokeApiKey
from ...types import Response


def _get_kwargs(
    app_id: str,
    key_id: str,
    *,
    authorization: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["authorization"] = authorization

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/apps/{app_id}/api-keys/{key_id}".format(
            app_id=quote(str(app_id), safe=""),
            key_id=quote(str(key_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | RevokeApiKeyResponseRevokeApiKey | None:
    if response.status_code == 200:
        response_200 = RevokeApiKeyResponseRevokeApiKey.from_dict(response.json())

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
) -> Response[HTTPValidationError | RevokeApiKeyResponseRevokeApiKey]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    app_id: str,
    key_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: str,
) -> Response[HTTPValidationError | RevokeApiKeyResponseRevokeApiKey]:
    """Revoke Api Key

     Revoke an API key. Requires admin role in org.

    Args:
        app_id (str):
        key_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RevokeApiKeyResponseRevokeApiKey]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        key_id=key_id,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    app_id: str,
    key_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: str,
) -> HTTPValidationError | RevokeApiKeyResponseRevokeApiKey | None:
    """Revoke Api Key

     Revoke an API key. Requires admin role in org.

    Args:
        app_id (str):
        key_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RevokeApiKeyResponseRevokeApiKey
    """

    return sync_detailed(
        app_id=app_id,
        key_id=key_id,
        client=client,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    app_id: str,
    key_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: str,
) -> Response[HTTPValidationError | RevokeApiKeyResponseRevokeApiKey]:
    """Revoke Api Key

     Revoke an API key. Requires admin role in org.

    Args:
        app_id (str):
        key_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | RevokeApiKeyResponseRevokeApiKey]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        key_id=key_id,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    app_id: str,
    key_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: str,
) -> HTTPValidationError | RevokeApiKeyResponseRevokeApiKey | None:
    """Revoke Api Key

     Revoke an API key. Requires admin role in org.

    Args:
        app_id (str):
        key_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | RevokeApiKeyResponseRevokeApiKey
    """

    return (
        await asyncio_detailed(
            app_id=app_id,
            key_id=key_id,
            client=client,
            authorization=authorization,
        )
    ).parsed
