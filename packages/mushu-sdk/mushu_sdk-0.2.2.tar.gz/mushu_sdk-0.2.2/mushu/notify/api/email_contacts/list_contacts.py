from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.contact_list_response import ContactListResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    app_id: str,
    *,
    user_id: None | str | Unset = UNSET,
    email: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization

    if not isinstance(x_api_key, Unset):
        headers["x-api-key"] = x_api_key

    params: dict[str, Any] = {}

    json_user_id: None | str | Unset
    if isinstance(user_id, Unset):
        json_user_id = UNSET
    else:
        json_user_id = user_id
    params["user_id"] = json_user_id

    json_email: None | str | Unset
    if isinstance(email, Unset):
        json_email = UNSET
    else:
        json_email = email
    params["email"] = json_email

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/apps/{app_id}/contacts".format(
            app_id=quote(str(app_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ContactListResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = ContactListResponse.from_dict(response.json())

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
) -> Response[ContactListResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    app_id: str,
    *,
    client: AuthenticatedClient | Client,
    user_id: None | str | Unset = UNSET,
    email: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Response[ContactListResponse | HTTPValidationError]:
    """List Contacts

     List email contacts.

    Filter by user_id to get a specific user's contacts,
    or by email to find which user owns an email.

    Args:
        app_id (str):
        user_id (None | str | Unset):
        email (None | str | Unset):
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ContactListResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        user_id=user_id,
        email=email,
        authorization=authorization,
        x_api_key=x_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    app_id: str,
    *,
    client: AuthenticatedClient | Client,
    user_id: None | str | Unset = UNSET,
    email: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> ContactListResponse | HTTPValidationError | None:
    """List Contacts

     List email contacts.

    Filter by user_id to get a specific user's contacts,
    or by email to find which user owns an email.

    Args:
        app_id (str):
        user_id (None | str | Unset):
        email (None | str | Unset):
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ContactListResponse | HTTPValidationError
    """

    return sync_detailed(
        app_id=app_id,
        client=client,
        user_id=user_id,
        email=email,
        authorization=authorization,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    app_id: str,
    *,
    client: AuthenticatedClient | Client,
    user_id: None | str | Unset = UNSET,
    email: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Response[ContactListResponse | HTTPValidationError]:
    """List Contacts

     List email contacts.

    Filter by user_id to get a specific user's contacts,
    or by email to find which user owns an email.

    Args:
        app_id (str):
        user_id (None | str | Unset):
        email (None | str | Unset):
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ContactListResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        user_id=user_id,
        email=email,
        authorization=authorization,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    app_id: str,
    *,
    client: AuthenticatedClient | Client,
    user_id: None | str | Unset = UNSET,
    email: None | str | Unset = UNSET,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> ContactListResponse | HTTPValidationError | None:
    """List Contacts

     List email contacts.

    Filter by user_id to get a specific user's contacts,
    or by email to find which user owns an email.

    Args:
        app_id (str):
        user_id (None | str | Unset):
        email (None | str | Unset):
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ContactListResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            app_id=app_id,
            client=client,
            user_id=user_id,
            email=email,
            authorization=authorization,
            x_api_key=x_api_key,
        )
    ).parsed
