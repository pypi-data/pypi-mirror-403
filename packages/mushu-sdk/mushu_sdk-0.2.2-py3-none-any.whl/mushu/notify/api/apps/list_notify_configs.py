from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.notify_config_list_response import NotifyConfigListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    org_id: None | str | Unset = UNSET,
    authorization: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["authorization"] = authorization

    params: dict[str, Any] = {}

    json_org_id: None | str | Unset
    if isinstance(org_id, Unset):
        json_org_id = UNSET
    else:
        json_org_id = org_id
    params["org_id"] = json_org_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/apps",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | NotifyConfigListResponse | None:
    if response.status_code == 200:
        response_200 = NotifyConfigListResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | NotifyConfigListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    org_id: None | str | Unset = UNSET,
    authorization: str,
) -> Response[HTTPValidationError | NotifyConfigListResponse]:
    """List Notify Configs

     List notification configs for an organization.

    Requires org_id parameter. User must be a member of the organization.

    Args:
        org_id (None | str | Unset):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | NotifyConfigListResponse]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    org_id: None | str | Unset = UNSET,
    authorization: str,
) -> HTTPValidationError | NotifyConfigListResponse | None:
    """List Notify Configs

     List notification configs for an organization.

    Requires org_id parameter. User must be a member of the organization.

    Args:
        org_id (None | str | Unset):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | NotifyConfigListResponse
    """

    return sync_detailed(
        client=client,
        org_id=org_id,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    org_id: None | str | Unset = UNSET,
    authorization: str,
) -> Response[HTTPValidationError | NotifyConfigListResponse]:
    """List Notify Configs

     List notification configs for an organization.

    Requires org_id parameter. User must be a member of the organization.

    Args:
        org_id (None | str | Unset):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | NotifyConfigListResponse]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    org_id: None | str | Unset = UNSET,
    authorization: str,
) -> HTTPValidationError | NotifyConfigListResponse | None:
    """List Notify Configs

     List notification configs for an organization.

    Requires org_id parameter. User must be a member of the organization.

    Args:
        org_id (None | str | Unset):
        authorization (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | NotifyConfigListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            org_id=org_id,
            authorization=authorization,
        )
    ).parsed
