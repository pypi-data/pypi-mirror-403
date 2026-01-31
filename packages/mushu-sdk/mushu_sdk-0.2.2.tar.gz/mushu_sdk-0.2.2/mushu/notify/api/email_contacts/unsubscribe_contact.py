from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.unsubscribe_contact_response_unsubscribe_contact import (
    UnsubscribeContactResponseUnsubscribeContact,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    app_id: str,
    email: str,
    *,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization

    if not isinstance(x_api_key, Unset):
        headers["x-api-key"] = x_api_key

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/apps/{app_id}/contacts/{email}".format(
            app_id=quote(str(app_id), safe=""),
            email=quote(str(email), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | UnsubscribeContactResponseUnsubscribeContact | None:
    if response.status_code == 200:
        response_200 = UnsubscribeContactResponseUnsubscribeContact.from_dict(response.json())

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
) -> Response[HTTPValidationError | UnsubscribeContactResponseUnsubscribeContact]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    app_id: str,
    email: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | UnsubscribeContactResponseUnsubscribeContact]:
    """Unsubscribe Contact

     Unsubscribe an email contact.

    The contact record is kept but marked as unsubscribed.
    Unsubscribed contacts will not receive emails.

    Args:
        app_id (str):
        email (str):
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | UnsubscribeContactResponseUnsubscribeContact]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
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
    email: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> HTTPValidationError | UnsubscribeContactResponseUnsubscribeContact | None:
    """Unsubscribe Contact

     Unsubscribe an email contact.

    The contact record is kept but marked as unsubscribed.
    Unsubscribed contacts will not receive emails.

    Args:
        app_id (str):
        email (str):
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | UnsubscribeContactResponseUnsubscribeContact
    """

    return sync_detailed(
        app_id=app_id,
        email=email,
        client=client,
        authorization=authorization,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    app_id: str,
    email: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | UnsubscribeContactResponseUnsubscribeContact]:
    """Unsubscribe Contact

     Unsubscribe an email contact.

    The contact record is kept but marked as unsubscribed.
    Unsubscribed contacts will not receive emails.

    Args:
        app_id (str):
        email (str):
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | UnsubscribeContactResponseUnsubscribeContact]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        email=email,
        authorization=authorization,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    app_id: str,
    email: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: None | str | Unset = UNSET,
    x_api_key: None | str | Unset = UNSET,
) -> HTTPValidationError | UnsubscribeContactResponseUnsubscribeContact | None:
    """Unsubscribe Contact

     Unsubscribe an email contact.

    The contact record is kept but marked as unsubscribed.
    Unsubscribed contacts will not receive emails.

    Args:
        app_id (str):
        email (str):
        authorization (None | str | Unset):
        x_api_key (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | UnsubscribeContactResponseUnsubscribeContact
    """

    return (
        await asyncio_detailed(
            app_id=app_id,
            email=email,
            client=client,
            authorization=authorization,
            x_api_key=x_api_key,
        )
    ).parsed
