from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.autocomplete_request import AutocompleteRequest
from ...models.autocomplete_response import AutocompleteResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: AutocompleteRequest,
    x_api_key: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_api_key, Unset):
        headers["X-API-Key"] = x_api_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/location/autocomplete",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AutocompleteResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = AutocompleteResponse.from_dict(response.json())

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
) -> Response[AutocompleteResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AutocompleteRequest,
    x_api_key: None | str | Unset = UNSET,
) -> Response[AutocompleteResponse | HTTPValidationError]:
    """Place Autocomplete

     Search for places using autocomplete.

    Returns place suggestions matching the query, optionally biased by location.
    Requires API key authentication. Usage is tracked and billed at $0.001/search.

    Results are cached for 7 days to reduce API costs.

    Args:
        x_api_key (None | str | Unset):
        body (AutocompleteRequest): Request for place autocomplete search.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AutocompleteResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        x_api_key=x_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: AutocompleteRequest,
    x_api_key: None | str | Unset = UNSET,
) -> AutocompleteResponse | HTTPValidationError | None:
    """Place Autocomplete

     Search for places using autocomplete.

    Returns place suggestions matching the query, optionally biased by location.
    Requires API key authentication. Usage is tracked and billed at $0.001/search.

    Results are cached for 7 days to reduce API costs.

    Args:
        x_api_key (None | str | Unset):
        body (AutocompleteRequest): Request for place autocomplete search.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AutocompleteResponse | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AutocompleteRequest,
    x_api_key: None | str | Unset = UNSET,
) -> Response[AutocompleteResponse | HTTPValidationError]:
    """Place Autocomplete

     Search for places using autocomplete.

    Returns place suggestions matching the query, optionally biased by location.
    Requires API key authentication. Usage is tracked and billed at $0.001/search.

    Results are cached for 7 days to reduce API costs.

    Args:
        x_api_key (None | str | Unset):
        body (AutocompleteRequest): Request for place autocomplete search.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AutocompleteResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: AutocompleteRequest,
    x_api_key: None | str | Unset = UNSET,
) -> AutocompleteResponse | HTTPValidationError | None:
    """Place Autocomplete

     Search for places using autocomplete.

    Returns place suggestions matching the query, optionally biased by location.
    Requires API key authentication. Usage is tracked and billed at $0.001/search.

    Results are cached for 7 days to reduce API costs.

    Args:
        x_api_key (None | str | Unset):
        body (AutocompleteRequest): Request for place autocomplete search.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AutocompleteResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_key=x_api_key,
        )
    ).parsed
