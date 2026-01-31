from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.add_document_body import AddDocumentBody
from ...models.add_document_response_201 import AddDocumentResponse201
from ...types import UNSET, Response, Unset


def _get_kwargs(
    shipment_id: str,
    *,
    body: AddDocumentBody | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/shipments/{shipment_id}/documents".format(
            shipment_id=quote(str(shipment_id), safe=""),
        ),
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AddDocumentResponse201 | Any | None:
    if response.status_code == 201:
        response_201 = AddDocumentResponse201.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = cast(Any, None)
        return response_400

    if response.status_code == 404:
        response_404 = cast(Any, None)
        return response_404

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[AddDocumentResponse201 | Any]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    shipment_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: AddDocumentBody | Unset = UNSET,
) -> Response[AddDocumentResponse201 | Any]:
    """Add document

    Args:
        shipment_id (str):
        body (AddDocumentBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AddDocumentResponse201 | Any]
    """

    kwargs = _get_kwargs(
        shipment_id=shipment_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    shipment_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: AddDocumentBody | Unset = UNSET,
) -> AddDocumentResponse201 | Any | None:
    """Add document

    Args:
        shipment_id (str):
        body (AddDocumentBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AddDocumentResponse201 | Any
    """

    return sync_detailed(
        shipment_id=shipment_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    shipment_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: AddDocumentBody | Unset = UNSET,
) -> Response[AddDocumentResponse201 | Any]:
    """Add document

    Args:
        shipment_id (str):
        body (AddDocumentBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AddDocumentResponse201 | Any]
    """

    kwargs = _get_kwargs(
        shipment_id=shipment_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    shipment_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: AddDocumentBody | Unset = UNSET,
) -> AddDocumentResponse201 | Any | None:
    """Add document

    Args:
        shipment_id (str):
        body (AddDocumentBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AddDocumentResponse201 | Any
    """

    return (
        await asyncio_detailed(
            shipment_id=shipment_id,
            client=client,
            body=body,
        )
    ).parsed
