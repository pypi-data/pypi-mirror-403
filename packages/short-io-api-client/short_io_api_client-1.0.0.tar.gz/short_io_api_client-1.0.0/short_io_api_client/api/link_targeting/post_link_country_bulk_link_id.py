from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_link_country_bulk_link_id_body_item import PostLinkCountryBulkLinkIdBodyItem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    link_id: str,
    *,
    body: list[PostLinkCountryBulkLinkIdBodyItem] | Unset = UNSET,
    domain_id: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["domainId"] = domain_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/link_country/bulk/{link_id}".format(
            link_id=quote(str(link_id), safe=""),
        ),
        "params": params,
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = []
        for body_item_data in body:
            body_item = body_item_data.to_dict()
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
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: list[PostLinkCountryBulkLinkIdBodyItem] | Unset = UNSET,
    domain_id: str | Unset = UNSET,
) -> Response[Any]:
    """Create link countries in bulk

    Args:
        link_id (str):
        domain_id (str | Unset):
        body (list[PostLinkCountryBulkLinkIdBodyItem] | Unset):

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
    body: list[PostLinkCountryBulkLinkIdBodyItem] | Unset = UNSET,
    domain_id: str | Unset = UNSET,
) -> Response[Any]:
    """Create link countries in bulk

    Args:
        link_id (str):
        domain_id (str | Unset):
        body (list[PostLinkCountryBulkLinkIdBodyItem] | Unset):

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
