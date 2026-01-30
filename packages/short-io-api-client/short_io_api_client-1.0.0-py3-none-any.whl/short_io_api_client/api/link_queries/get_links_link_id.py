from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_links_link_id_response_200 import GetLinksLinkIdResponse200
from ...models.get_links_link_id_response_400 import GetLinksLinkIdResponse400
from ...models.get_links_link_id_response_403 import GetLinksLinkIdResponse403
from ...models.get_links_link_id_response_404 import GetLinksLinkIdResponse404
from ...types import UNSET, Response, Unset


def _get_kwargs(
    link_id: str,
    *,
    domain_id: str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["domainId"] = domain_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/links/{link_id}".format(
            link_id=quote(str(link_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetLinksLinkIdResponse200 | GetLinksLinkIdResponse400 | GetLinksLinkIdResponse403 | GetLinksLinkIdResponse404 | None
):
    if response.status_code == 200:
        response_200 = GetLinksLinkIdResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = GetLinksLinkIdResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 403:
        response_403 = GetLinksLinkIdResponse403.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = GetLinksLinkIdResponse404.from_dict(response.json())

        return response_404

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetLinksLinkIdResponse200 | GetLinksLinkIdResponse400 | GetLinksLinkIdResponse403 | GetLinksLinkIdResponse404
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
    domain_id: str | Unset = UNSET,
) -> Response[
    GetLinksLinkIdResponse200 | GetLinksLinkIdResponse400 | GetLinksLinkIdResponse403 | GetLinksLinkIdResponse404
]:
    """Get link info by link id

     Get link info by link id. Rate limit: 20/s

    Args:
        link_id (str):
        domain_id (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetLinksLinkIdResponse200 | GetLinksLinkIdResponse400 | GetLinksLinkIdResponse403 | GetLinksLinkIdResponse404]
    """

    kwargs = _get_kwargs(
        link_id=link_id,
        domain_id=domain_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
    domain_id: str | Unset = UNSET,
) -> (
    GetLinksLinkIdResponse200 | GetLinksLinkIdResponse400 | GetLinksLinkIdResponse403 | GetLinksLinkIdResponse404 | None
):
    """Get link info by link id

     Get link info by link id. Rate limit: 20/s

    Args:
        link_id (str):
        domain_id (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetLinksLinkIdResponse200 | GetLinksLinkIdResponse400 | GetLinksLinkIdResponse403 | GetLinksLinkIdResponse404
    """

    return sync_detailed(
        link_id=link_id,
        client=client,
        domain_id=domain_id,
    ).parsed


async def asyncio_detailed(
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
    domain_id: str | Unset = UNSET,
) -> Response[
    GetLinksLinkIdResponse200 | GetLinksLinkIdResponse400 | GetLinksLinkIdResponse403 | GetLinksLinkIdResponse404
]:
    """Get link info by link id

     Get link info by link id. Rate limit: 20/s

    Args:
        link_id (str):
        domain_id (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetLinksLinkIdResponse200 | GetLinksLinkIdResponse400 | GetLinksLinkIdResponse403 | GetLinksLinkIdResponse404]
    """

    kwargs = _get_kwargs(
        link_id=link_id,
        domain_id=domain_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
    domain_id: str | Unset = UNSET,
) -> (
    GetLinksLinkIdResponse200 | GetLinksLinkIdResponse400 | GetLinksLinkIdResponse403 | GetLinksLinkIdResponse404 | None
):
    """Get link info by link id

     Get link info by link id. Rate limit: 20/s

    Args:
        link_id (str):
        domain_id (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetLinksLinkIdResponse200 | GetLinksLinkIdResponse400 | GetLinksLinkIdResponse403 | GetLinksLinkIdResponse404
    """

    return (
        await asyncio_detailed(
            link_id=link_id,
            client=client,
            domain_id=domain_id,
        )
    ).parsed
