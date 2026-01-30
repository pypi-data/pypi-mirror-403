from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_link_region_link_id_body import PostLinkRegionLinkIdBody
from ...types import UNSET, Response, Unset


def _get_kwargs(
    link_id: str,
    *,
    body: PostLinkRegionLinkIdBody,
    domain_id: int | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["domainId"] = domain_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/link_region/{link_id}".format(
            link_id=quote(str(link_id), safe=""),
        ),
        "params": params,
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
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PostLinkRegionLinkIdBody,
    domain_id: int | Unset = UNSET,
) -> Response[Any]:
    """Add region targeting to link

     Add region targeting to link

    Args:
        link_id (str):
        domain_id (int | Unset):
        body (PostLinkRegionLinkIdBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        link_id=link_id,
        body=body,
        domain_id=domain_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PostLinkRegionLinkIdBody,
    domain_id: int | Unset = UNSET,
) -> Response[Any]:
    """Add region targeting to link

     Add region targeting to link

    Args:
        link_id (str):
        domain_id (int | Unset):
        body (PostLinkRegionLinkIdBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        link_id=link_id,
        body=body,
        domain_id=domain_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)
