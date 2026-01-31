from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_label_body import GetLabelBody
from ...models.get_label_response_200 import GetLabelResponse200
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: GetLabelBody | Unset = UNSET,
    client_header: int,
    apikey: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["client"] = str(client_header)

    headers["apikey"] = apikey

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/getLabel",
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | GetLabelResponse200 | None:
    if response.status_code == 200:
        response_200 = GetLabelResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = cast(Any, None)
        return response_400

    if response.status_code == 401:
        response_401 = cast(Any, None)
        return response_401

    if response.status_code == 404:
        response_404 = cast(Any, None)
        return response_404

    if response.status_code == 409:
        response_409 = cast(Any, None)
        return response_409

    if response.status_code == 422:
        response_422 = cast(Any, None)
        return response_422

    if response.status_code == 429:
        response_429 = cast(Any, None)
        return response_429

    if response.status_code == 503:
        response_503 = cast(Any, None)
        return response_503

    if 400 <= response.status_code <= 499:
        response_4xx = cast(Any, None)
        return response_4xx

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | GetLabelResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: GetLabelBody | Unset = UNSET,
    client_header: int,
    apikey: str,
) -> Response[Any | GetLabelResponse200]:
    """Get Label

     Receive the PDF or ZPL labels for shipments, only possible when the shipment is booked to the
    carrier.
    Note: insert/updateShipment action book directly respond directly with the PDF/ZPL label

    The type of label (PDF or ZPL) depends on the response and capabilities of the carrier.

    Args:
        client_header (int):
        apikey (str):
        body (GetLabelBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | GetLabelResponse200]
    """

    kwargs = _get_kwargs(
        body=body,
        client_header=client_header,
        apikey=apikey,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: GetLabelBody | Unset = UNSET,
    client_header: int,
    apikey: str,
) -> Any | GetLabelResponse200 | None:
    """Get Label

     Receive the PDF or ZPL labels for shipments, only possible when the shipment is booked to the
    carrier.
    Note: insert/updateShipment action book directly respond directly with the PDF/ZPL label

    The type of label (PDF or ZPL) depends on the response and capabilities of the carrier.

    Args:
        client_header (int):
        apikey (str):
        body (GetLabelBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | GetLabelResponse200
    """

    return sync_detailed(
        client=client,
        body=body,
        client_header=client_header,
        apikey=apikey,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: GetLabelBody | Unset = UNSET,
    client_header: int,
    apikey: str,
) -> Response[Any | GetLabelResponse200]:
    """Get Label

     Receive the PDF or ZPL labels for shipments, only possible when the shipment is booked to the
    carrier.
    Note: insert/updateShipment action book directly respond directly with the PDF/ZPL label

    The type of label (PDF or ZPL) depends on the response and capabilities of the carrier.

    Args:
        client_header (int):
        apikey (str):
        body (GetLabelBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | GetLabelResponse200]
    """

    kwargs = _get_kwargs(
        body=body,
        client_header=client_header,
        apikey=apikey,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: GetLabelBody | Unset = UNSET,
    client_header: int,
    apikey: str,
) -> Any | GetLabelResponse200 | None:
    """Get Label

     Receive the PDF or ZPL labels for shipments, only possible when the shipment is booked to the
    carrier.
    Note: insert/updateShipment action book directly respond directly with the PDF/ZPL label

    The type of label (PDF or ZPL) depends on the response and capabilities of the carrier.

    Args:
        client_header (int):
        apikey (str):
        body (GetLabelBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | GetLabelResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            client_header=client_header,
            apikey=apikey,
        )
    ).parsed
