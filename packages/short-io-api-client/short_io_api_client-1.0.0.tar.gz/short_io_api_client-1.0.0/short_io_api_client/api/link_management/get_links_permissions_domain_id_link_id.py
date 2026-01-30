from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_links_permissions_domain_id_link_id_response_200_item import (
    GetLinksPermissionsDomainIdLinkIdResponse200Item,
)
from ...models.get_links_permissions_domain_id_link_id_response_403 import GetLinksPermissionsDomainIdLinkIdResponse403
from ...models.get_links_permissions_domain_id_link_id_response_404 import GetLinksPermissionsDomainIdLinkIdResponse404
from ...types import Response


def _get_kwargs(
    domain_id: str,
    link_id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/links/permissions/{domain_id}/{link_id}".format(
            domain_id=quote(str(domain_id), safe=""),
            link_id=quote(str(link_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetLinksPermissionsDomainIdLinkIdResponse403
    | GetLinksPermissionsDomainIdLinkIdResponse404
    | list[GetLinksPermissionsDomainIdLinkIdResponse200Item]
    | None
):
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = GetLinksPermissionsDomainIdLinkIdResponse200Item.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if response.status_code == 403:
        response_403 = GetLinksPermissionsDomainIdLinkIdResponse403.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = GetLinksPermissionsDomainIdLinkIdResponse404.from_dict(response.json())

        return response_404

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetLinksPermissionsDomainIdLinkIdResponse403
    | GetLinksPermissionsDomainIdLinkIdResponse404
    | list[GetLinksPermissionsDomainIdLinkIdResponse200Item]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    domain_id: str,
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    GetLinksPermissionsDomainIdLinkIdResponse403
    | GetLinksPermissionsDomainIdLinkIdResponse404
    | list[GetLinksPermissionsDomainIdLinkIdResponse200Item]
]:
    """Get link permissions

    Args:
        domain_id (str):
        link_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetLinksPermissionsDomainIdLinkIdResponse403 | GetLinksPermissionsDomainIdLinkIdResponse404 | list[GetLinksPermissionsDomainIdLinkIdResponse200Item]]
    """

    kwargs = _get_kwargs(
        domain_id=domain_id,
        link_id=link_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    domain_id: str,
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    GetLinksPermissionsDomainIdLinkIdResponse403
    | GetLinksPermissionsDomainIdLinkIdResponse404
    | list[GetLinksPermissionsDomainIdLinkIdResponse200Item]
    | None
):
    """Get link permissions

    Args:
        domain_id (str):
        link_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetLinksPermissionsDomainIdLinkIdResponse403 | GetLinksPermissionsDomainIdLinkIdResponse404 | list[GetLinksPermissionsDomainIdLinkIdResponse200Item]
    """

    return sync_detailed(
        domain_id=domain_id,
        link_id=link_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    domain_id: str,
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    GetLinksPermissionsDomainIdLinkIdResponse403
    | GetLinksPermissionsDomainIdLinkIdResponse404
    | list[GetLinksPermissionsDomainIdLinkIdResponse200Item]
]:
    """Get link permissions

    Args:
        domain_id (str):
        link_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetLinksPermissionsDomainIdLinkIdResponse403 | GetLinksPermissionsDomainIdLinkIdResponse404 | list[GetLinksPermissionsDomainIdLinkIdResponse200Item]]
    """

    kwargs = _get_kwargs(
        domain_id=domain_id,
        link_id=link_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    domain_id: str,
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    GetLinksPermissionsDomainIdLinkIdResponse403
    | GetLinksPermissionsDomainIdLinkIdResponse404
    | list[GetLinksPermissionsDomainIdLinkIdResponse200Item]
    | None
):
    """Get link permissions

    Args:
        domain_id (str):
        link_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetLinksPermissionsDomainIdLinkIdResponse403 | GetLinksPermissionsDomainIdLinkIdResponse404 | list[GetLinksPermissionsDomainIdLinkIdResponse200Item]
    """

    return (
        await asyncio_detailed(
            domain_id=domain_id,
            link_id=link_id,
            client=client,
        )
    ).parsed
