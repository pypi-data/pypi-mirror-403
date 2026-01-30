from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.put_links_opengraph_domain_id_link_id_body_item_item_type_0 import (
    PutLinksOpengraphDomainIdLinkIdBodyItemItemType0,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    domain_id: float,
    link_id: str,
    *,
    body: list[list[Any | PutLinksOpengraphDomainIdLinkIdBodyItemItemType0 | str]] | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/links/opengraph/{domain_id}/{link_id}".format(
            domain_id=quote(str(domain_id), safe=""),
            link_id=quote(str(link_id), safe=""),
        ),
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = []
        for body_item_data in body:
            body_item = []
            for body_item_item_data in body_item_data:
                body_item_item: Any | str
                if isinstance(body_item_item_data, PutLinksOpengraphDomainIdLinkIdBodyItemItemType0):
                    body_item_item = body_item_item_data.value
                else:
                    body_item_item = body_item_item_data
                body_item.append(body_item_item)

            _kwargs["json"].append(body_item)

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
    domain_id: float,
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: list[list[Any | PutLinksOpengraphDomainIdLinkIdBodyItemItemType0 | str]] | Unset = UNSET,
) -> Response[Any]:
    """Set link opengraph properties

    Args:
        domain_id (float):
        link_id (str):
        body (list[list[Any | PutLinksOpengraphDomainIdLinkIdBodyItemItemType0 | str]] | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        domain_id=domain_id,
        link_id=link_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    domain_id: float,
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: list[list[Any | PutLinksOpengraphDomainIdLinkIdBodyItemItemType0 | str]] | Unset = UNSET,
) -> Response[Any]:
    """Set link opengraph properties

    Args:
        domain_id (float):
        link_id (str):
        body (list[list[Any | PutLinksOpengraphDomainIdLinkIdBodyItemItemType0 | str]] | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        domain_id=domain_id,
        link_id=link_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)
