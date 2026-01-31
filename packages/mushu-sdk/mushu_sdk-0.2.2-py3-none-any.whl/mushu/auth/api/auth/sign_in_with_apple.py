from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.apple_sign_in_request import AppleSignInRequest
from ...models.http_validation_error import HTTPValidationError
from ...models.session_response import SessionResponse
from ...types import Response


def _get_kwargs(
    *,
    body: AppleSignInRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/auth/apple",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | SessionResponse | None:
    if response.status_code == 200:
        response_200 = SessionResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | SessionResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AppleSignInRequest,
) -> Response[HTTPValidationError | SessionResponse]:
    """Sign In With Apple

     Sign in with Apple.

    Exchange Apple ID token and authorization code for session tokens.
    Creates user account on first sign in.

    The app is determined from the client_id (bundle ID) in the token.
    If no app is configured for this bundle ID, the platform app is used.

    Args:
        body (AppleSignInRequest): Request to sign in with Apple.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SessionResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: AppleSignInRequest,
) -> HTTPValidationError | SessionResponse | None:
    """Sign In With Apple

     Sign in with Apple.

    Exchange Apple ID token and authorization code for session tokens.
    Creates user account on first sign in.

    The app is determined from the client_id (bundle ID) in the token.
    If no app is configured for this bundle ID, the platform app is used.

    Args:
        body (AppleSignInRequest): Request to sign in with Apple.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SessionResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AppleSignInRequest,
) -> Response[HTTPValidationError | SessionResponse]:
    """Sign In With Apple

     Sign in with Apple.

    Exchange Apple ID token and authorization code for session tokens.
    Creates user account on first sign in.

    The app is determined from the client_id (bundle ID) in the token.
    If no app is configured for this bundle ID, the platform app is used.

    Args:
        body (AppleSignInRequest): Request to sign in with Apple.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SessionResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: AppleSignInRequest,
) -> HTTPValidationError | SessionResponse | None:
    """Sign In With Apple

     Sign in with Apple.

    Exchange Apple ID token and authorization code for session tokens.
    Creates user account on first sign in.

    The app is determined from the client_id (bundle ID) in the token.
    If no app is configured for this bundle ID, the platform app is used.

    Args:
        body (AppleSignInRequest): Request to sign in with Apple.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SessionResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
