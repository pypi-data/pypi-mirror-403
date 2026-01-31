from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.app import App
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    bundle_id: str,
    *,
    authorization: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["authorization"] = authorization

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/apps/by-bundle/{bundle_id}".format(
            bundle_id=quote(str(bundle_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> App | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = App.from_dict(response.json())

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
) -> Response[App | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    bundle_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: str,
) -> Response[App | HTTPValidationError]:
    """Get App By Bundle Id

     Get app by bundle ID.

    Args:
        bundle_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[App | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        bundle_id=bundle_id,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    bundle_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: str,
) -> App | HTTPValidationError | None:
    """Get App By Bundle Id

     Get app by bundle ID.

    Args:
        bundle_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        App | HTTPValidationError
    """

    return sync_detailed(
        bundle_id=bundle_id,
        client=client,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    bundle_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: str,
) -> Response[App | HTTPValidationError]:
    """Get App By Bundle Id

     Get app by bundle ID.

    Args:
        bundle_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[App | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        bundle_id=bundle_id,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    bundle_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: str,
) -> App | HTTPValidationError | None:
    """Get App By Bundle Id

     Get app by bundle ID.

    Args:
        bundle_id (str):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        App | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            bundle_id=bundle_id,
            client=client,
            authorization=authorization,
        )
    ).parsed
