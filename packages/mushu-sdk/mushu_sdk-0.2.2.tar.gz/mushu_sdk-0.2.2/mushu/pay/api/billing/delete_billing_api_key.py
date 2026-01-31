from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_billing_api_key_response_delete_billing_api_key import (
    DeleteBillingApiKeyResponseDeleteBillingApiKey,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    org_id: str,
    key_id: str,
    *,
    authorization: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["authorization"] = authorization

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/orgs/{org_id}/billing/api-keys/{key_id}".format(
            org_id=quote(str(org_id), safe=""),
            key_id=quote(str(key_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DeleteBillingApiKeyResponseDeleteBillingApiKey | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = DeleteBillingApiKeyResponseDeleteBillingApiKey.from_dict(response.json())

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
) -> Response[DeleteBillingApiKeyResponseDeleteBillingApiKey | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    org_id: str,
    key_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: str,
) -> Response[DeleteBillingApiKeyResponseDeleteBillingApiKey | HTTPValidationError]:
    """Delete Api Key

     Delete an API key.

    Args:
        org_id (str):
        key_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteBillingApiKeyResponseDeleteBillingApiKey | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        key_id=key_id,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    org_id: str,
    key_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: str,
) -> DeleteBillingApiKeyResponseDeleteBillingApiKey | HTTPValidationError | None:
    """Delete Api Key

     Delete an API key.

    Args:
        org_id (str):
        key_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteBillingApiKeyResponseDeleteBillingApiKey | HTTPValidationError
    """

    return sync_detailed(
        org_id=org_id,
        key_id=key_id,
        client=client,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    org_id: str,
    key_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: str,
) -> Response[DeleteBillingApiKeyResponseDeleteBillingApiKey | HTTPValidationError]:
    """Delete Api Key

     Delete an API key.

    Args:
        org_id (str):
        key_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteBillingApiKeyResponseDeleteBillingApiKey | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        key_id=key_id,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    org_id: str,
    key_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: str,
) -> DeleteBillingApiKeyResponseDeleteBillingApiKey | HTTPValidationError | None:
    """Delete Api Key

     Delete an API key.

    Args:
        org_id (str):
        key_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteBillingApiKeyResponseDeleteBillingApiKey | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            org_id=org_id,
            key_id=key_id,
            client=client,
            authorization=authorization,
        )
    ).parsed
