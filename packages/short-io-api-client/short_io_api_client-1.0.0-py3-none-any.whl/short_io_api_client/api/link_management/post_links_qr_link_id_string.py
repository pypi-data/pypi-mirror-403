from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_links_qr_link_id_string_body import PostLinksQrLinkIdStringBody
from ...types import UNSET, Response, Unset


def _get_kwargs(
    link_id_string: str,
    *,
    body: PostLinksQrLinkIdStringBody,
    accept: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(accept, Unset):
        headers["accept"] = accept

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/links/qr/{link_id_string}".format(
            link_id_string=quote(str(link_id_string), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | None:
    if response.status_code == 200:
        return None

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    link_id_string: str,
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksQrLinkIdStringBody,
    accept: str | Unset = UNSET,
) -> Response[Any]:
    """Generate QR code for the link

    Args:
        link_id_string (str):
        accept (str | Unset):
        body (PostLinksQrLinkIdStringBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        link_id_string=link_id_string,
        body=body,
        accept=accept,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    link_id_string: str,
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksQrLinkIdStringBody,
    accept: str | Unset = UNSET,
) -> Response[Any]:
    """Generate QR code for the link

    Args:
        link_id_string (str):
        accept (str | Unset):
        body (PostLinksQrLinkIdStringBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        link_id_string=link_id_string,
        body=body,
        accept=accept,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)
