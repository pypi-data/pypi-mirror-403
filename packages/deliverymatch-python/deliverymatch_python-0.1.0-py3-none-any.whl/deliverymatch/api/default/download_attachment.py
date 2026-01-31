from http import HTTPStatus
from io import BytesIO
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.download_attachment_body import DownloadAttachmentBody
from ...types import UNSET, File, Response, Unset


def _get_kwargs(
    *,
    body: DownloadAttachmentBody | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/downloadAttachment",
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> File | None:
    if response.status_code == 200:
        response_200 = File(payload=BytesIO(response.content))

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[File]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DownloadAttachmentBody | Unset = UNSET,
) -> Response[File]:
    r"""Download Attachment

     Allows extra documents to be returned in the API responses.

    **Important:** this feature only works if enabled. Contact <a
    href=\"https://www.deliverymatch.eu/support/\">support</a> for more information

    Args:
        body (DownloadAttachmentBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[File]
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
    body: DownloadAttachmentBody | Unset = UNSET,
) -> File | None:
    r"""Download Attachment

     Allows extra documents to be returned in the API responses.

    **Important:** this feature only works if enabled. Contact <a
    href=\"https://www.deliverymatch.eu/support/\">support</a> for more information

    Args:
        body (DownloadAttachmentBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        File
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DownloadAttachmentBody | Unset = UNSET,
) -> Response[File]:
    r"""Download Attachment

     Allows extra documents to be returned in the API responses.

    **Important:** this feature only works if enabled. Contact <a
    href=\"https://www.deliverymatch.eu/support/\">support</a> for more information

    Args:
        body (DownloadAttachmentBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[File]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: DownloadAttachmentBody | Unset = UNSET,
) -> File | None:
    r"""Download Attachment

     Allows extra documents to be returned in the API responses.

    **Important:** this feature only works if enabled. Contact <a
    href=\"https://www.deliverymatch.eu/support/\">support</a> for more information

    Args:
        body (DownloadAttachmentBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        File
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
