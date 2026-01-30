from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_domains_domain_id_response_200 import GetDomainsDomainIdResponse200
from ...models.get_domains_domain_id_response_403 import GetDomainsDomainIdResponse403
from ...types import Response


def _get_kwargs(
    domain_id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/domains/{domain_id}".format(
            domain_id=quote(str(domain_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GetDomainsDomainIdResponse200 | GetDomainsDomainIdResponse403 | None:
    if response.status_code == 200:
        response_200 = GetDomainsDomainIdResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 403:
        response_403 = GetDomainsDomainIdResponse403.from_dict(response.json())

        return response_403

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[GetDomainsDomainIdResponse200 | GetDomainsDomainIdResponse403]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    domain_id: int,
    *,
    client: AuthenticatedClient | Client,
) -> Response[GetDomainsDomainIdResponse200 | GetDomainsDomainIdResponse403]:
    """Get domain details by id

    Args:
        domain_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetDomainsDomainIdResponse200 | GetDomainsDomainIdResponse403]
    """

    kwargs = _get_kwargs(
        domain_id=domain_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    domain_id: int,
    *,
    client: AuthenticatedClient | Client,
) -> GetDomainsDomainIdResponse200 | GetDomainsDomainIdResponse403 | None:
    """Get domain details by id

    Args:
        domain_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetDomainsDomainIdResponse200 | GetDomainsDomainIdResponse403
    """

    return sync_detailed(
        domain_id=domain_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    domain_id: int,
    *,
    client: AuthenticatedClient | Client,
) -> Response[GetDomainsDomainIdResponse200 | GetDomainsDomainIdResponse403]:
    """Get domain details by id

    Args:
        domain_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetDomainsDomainIdResponse200 | GetDomainsDomainIdResponse403]
    """

    kwargs = _get_kwargs(
        domain_id=domain_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    domain_id: int,
    *,
    client: AuthenticatedClient | Client,
) -> GetDomainsDomainIdResponse200 | GetDomainsDomainIdResponse403 | None:
    """Get domain details by id

    Args:
        domain_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetDomainsDomainIdResponse200 | GetDomainsDomainIdResponse403
    """

    return (
        await asyncio_detailed(
            domain_id=domain_id,
            client=client,
        )
    ).parsed
