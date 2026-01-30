from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_link_country_link_id_country_country import DeleteLinkCountryLinkIdCountryCountry
from ...types import UNSET, Response, Unset


def _get_kwargs(
    link_id: str,
    country: DeleteLinkCountryLinkIdCountryCountry,
    *,
    domain_id: str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["domainId"] = domain_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/link_country/{link_id}/{country}".format(
            link_id=quote(str(link_id), safe=""),
            country=quote(str(country), safe=""),
        ),
        "params": params,
    }

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
    country: DeleteLinkCountryLinkIdCountryCountry,
    *,
    client: AuthenticatedClient | Client,
    domain_id: str | Unset = UNSET,
) -> Response[Any]:
    """Delete link country

    Args:
        link_id (str):
        country (DeleteLinkCountryLinkIdCountryCountry):
        domain_id (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        link_id=link_id,
        country=country,
        domain_id=domain_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    link_id: str,
    country: DeleteLinkCountryLinkIdCountryCountry,
    *,
    client: AuthenticatedClient | Client,
    domain_id: str | Unset = UNSET,
) -> Response[Any]:
    """Delete link country

    Args:
        link_id (str):
        country (DeleteLinkCountryLinkIdCountryCountry):
        domain_id (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        link_id=link_id,
        country=country,
        domain_id=domain_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)
