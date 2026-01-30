from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_links_permissions_domain_id_link_id_user_id_response_201 import (
    PostLinksPermissionsDomainIdLinkIdUserIdResponse201,
)
from ...models.post_links_permissions_domain_id_link_id_user_id_response_400 import (
    PostLinksPermissionsDomainIdLinkIdUserIdResponse400,
)
from ...models.post_links_permissions_domain_id_link_id_user_id_response_402 import (
    PostLinksPermissionsDomainIdLinkIdUserIdResponse402,
)
from ...models.post_links_permissions_domain_id_link_id_user_id_response_403 import (
    PostLinksPermissionsDomainIdLinkIdUserIdResponse403,
)
from ...models.post_links_permissions_domain_id_link_id_user_id_response_404 import (
    PostLinksPermissionsDomainIdLinkIdUserIdResponse404,
)
from ...types import Response


def _get_kwargs(
    domain_id: str,
    link_id: str,
    user_id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/links/permissions/{domain_id}/{link_id}/{user_id}".format(
            domain_id=quote(str(domain_id), safe=""),
            link_id=quote(str(link_id), safe=""),
            user_id=quote(str(user_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    PostLinksPermissionsDomainIdLinkIdUserIdResponse201
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse400
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse402
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse403
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse404
    | None
):
    if response.status_code == 201:
        response_201 = PostLinksPermissionsDomainIdLinkIdUserIdResponse201.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = PostLinksPermissionsDomainIdLinkIdUserIdResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 402:
        response_402 = PostLinksPermissionsDomainIdLinkIdUserIdResponse402.from_dict(response.json())

        return response_402

    if response.status_code == 403:
        response_403 = PostLinksPermissionsDomainIdLinkIdUserIdResponse403.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = PostLinksPermissionsDomainIdLinkIdUserIdResponse404.from_dict(response.json())

        return response_404

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    PostLinksPermissionsDomainIdLinkIdUserIdResponse201
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse400
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse402
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse403
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse404
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
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    PostLinksPermissionsDomainIdLinkIdUserIdResponse201
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse400
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse402
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse403
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse404
]:
    """Add link permission

    Args:
        domain_id (str):
        link_id (str):
        user_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostLinksPermissionsDomainIdLinkIdUserIdResponse201 | PostLinksPermissionsDomainIdLinkIdUserIdResponse400 | PostLinksPermissionsDomainIdLinkIdUserIdResponse402 | PostLinksPermissionsDomainIdLinkIdUserIdResponse403 | PostLinksPermissionsDomainIdLinkIdUserIdResponse404]
    """

    kwargs = _get_kwargs(
        domain_id=domain_id,
        link_id=link_id,
        user_id=user_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    domain_id: str,
    link_id: str,
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    PostLinksPermissionsDomainIdLinkIdUserIdResponse201
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse400
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse402
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse403
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse404
    | None
):
    """Add link permission

    Args:
        domain_id (str):
        link_id (str):
        user_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostLinksPermissionsDomainIdLinkIdUserIdResponse201 | PostLinksPermissionsDomainIdLinkIdUserIdResponse400 | PostLinksPermissionsDomainIdLinkIdUserIdResponse402 | PostLinksPermissionsDomainIdLinkIdUserIdResponse403 | PostLinksPermissionsDomainIdLinkIdUserIdResponse404
    """

    return sync_detailed(
        domain_id=domain_id,
        link_id=link_id,
        user_id=user_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    domain_id: str,
    link_id: str,
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    PostLinksPermissionsDomainIdLinkIdUserIdResponse201
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse400
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse402
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse403
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse404
]:
    """Add link permission

    Args:
        domain_id (str):
        link_id (str):
        user_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostLinksPermissionsDomainIdLinkIdUserIdResponse201 | PostLinksPermissionsDomainIdLinkIdUserIdResponse400 | PostLinksPermissionsDomainIdLinkIdUserIdResponse402 | PostLinksPermissionsDomainIdLinkIdUserIdResponse403 | PostLinksPermissionsDomainIdLinkIdUserIdResponse404]
    """

    kwargs = _get_kwargs(
        domain_id=domain_id,
        link_id=link_id,
        user_id=user_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    domain_id: str,
    link_id: str,
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    PostLinksPermissionsDomainIdLinkIdUserIdResponse201
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse400
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse402
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse403
    | PostLinksPermissionsDomainIdLinkIdUserIdResponse404
    | None
):
    """Add link permission

    Args:
        domain_id (str):
        link_id (str):
        user_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostLinksPermissionsDomainIdLinkIdUserIdResponse201 | PostLinksPermissionsDomainIdLinkIdUserIdResponse400 | PostLinksPermissionsDomainIdLinkIdUserIdResponse402 | PostLinksPermissionsDomainIdLinkIdUserIdResponse403 | PostLinksPermissionsDomainIdLinkIdUserIdResponse404
    """

    return (
        await asyncio_detailed(
            domain_id=domain_id,
            link_id=link_id,
            user_id=user_id,
            client=client,
        )
    ).parsed
