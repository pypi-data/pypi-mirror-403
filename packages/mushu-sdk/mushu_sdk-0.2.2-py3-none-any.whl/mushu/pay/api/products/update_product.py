from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.pay_product import PayProduct
from ...models.update_product_request import UpdateProductRequest
from ...types import Response


def _get_kwargs(
    org_id: str,
    product_id: str,
    *,
    body: UpdateProductRequest,
    authorization: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["authorization"] = authorization

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/orgs/{org_id}/products/{product_id}".format(
            org_id=quote(str(org_id), safe=""),
            product_id=quote(str(product_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | PayProduct | None:
    if response.status_code == 200:
        response_200 = PayProduct.from_dict(response.json())

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
) -> Response[HTTPValidationError | PayProduct]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    org_id: str,
    product_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateProductRequest,
    authorization: str,
) -> Response[HTTPValidationError | PayProduct]:
    """Update Product

     Update a product.

    Args:
        org_id (str):
        product_id (str):
        authorization (str):
        body (UpdateProductRequest): Request to update a product.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PayProduct]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        product_id=product_id,
        body=body,
        authorization=authorization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    org_id: str,
    product_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateProductRequest,
    authorization: str,
) -> HTTPValidationError | PayProduct | None:
    """Update Product

     Update a product.

    Args:
        org_id (str):
        product_id (str):
        authorization (str):
        body (UpdateProductRequest): Request to update a product.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PayProduct
    """

    return sync_detailed(
        org_id=org_id,
        product_id=product_id,
        client=client,
        body=body,
        authorization=authorization,
    ).parsed


async def asyncio_detailed(
    org_id: str,
    product_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateProductRequest,
    authorization: str,
) -> Response[HTTPValidationError | PayProduct]:
    """Update Product

     Update a product.

    Args:
        org_id (str):
        product_id (str):
        authorization (str):
        body (UpdateProductRequest): Request to update a product.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PayProduct]
    """

    kwargs = _get_kwargs(
        org_id=org_id,
        product_id=product_id,
        body=body,
        authorization=authorization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    org_id: str,
    product_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateProductRequest,
    authorization: str,
) -> HTTPValidationError | PayProduct | None:
    """Update Product

     Update a product.

    Args:
        org_id (str):
        product_id (str):
        authorization (str):
        body (UpdateProductRequest): Request to update a product.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PayProduct
    """

    return (
        await asyncio_detailed(
            org_id=org_id,
            product_id=product_id,
            client=client,
            body=body,
            authorization=authorization,
        )
    ).parsed
