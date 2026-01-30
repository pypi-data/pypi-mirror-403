from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_domains_settings_domain_id_body import PostDomainsSettingsDomainIdBody
from ...models.post_domains_settings_domain_id_response_200 import PostDomainsSettingsDomainIdResponse200
from ...models.post_domains_settings_domain_id_response_400 import PostDomainsSettingsDomainIdResponse400
from ...models.post_domains_settings_domain_id_response_401 import PostDomainsSettingsDomainIdResponse401
from ...models.post_domains_settings_domain_id_response_402 import PostDomainsSettingsDomainIdResponse402
from ...models.post_domains_settings_domain_id_response_403 import PostDomainsSettingsDomainIdResponse403
from ...models.post_domains_settings_domain_id_response_404 import PostDomainsSettingsDomainIdResponse404
from ...types import UNSET, Response, Unset


def _get_kwargs(
    domain_id: int,
    *,
    body: PostDomainsSettingsDomainIdBody | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/domains/settings/{domain_id}".format(
            domain_id=quote(str(domain_id), safe=""),
        ),
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    PostDomainsSettingsDomainIdResponse200
    | PostDomainsSettingsDomainIdResponse400
    | PostDomainsSettingsDomainIdResponse401
    | PostDomainsSettingsDomainIdResponse402
    | PostDomainsSettingsDomainIdResponse403
    | PostDomainsSettingsDomainIdResponse404
    | None
):
    if response.status_code == 200:
        response_200 = PostDomainsSettingsDomainIdResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = PostDomainsSettingsDomainIdResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = PostDomainsSettingsDomainIdResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 402:
        response_402 = PostDomainsSettingsDomainIdResponse402.from_dict(response.json())

        return response_402

    if response.status_code == 403:
        response_403 = PostDomainsSettingsDomainIdResponse403.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = PostDomainsSettingsDomainIdResponse404.from_dict(response.json())

        return response_404

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    PostDomainsSettingsDomainIdResponse200
    | PostDomainsSettingsDomainIdResponse400
    | PostDomainsSettingsDomainIdResponse401
    | PostDomainsSettingsDomainIdResponse402
    | PostDomainsSettingsDomainIdResponse403
    | PostDomainsSettingsDomainIdResponse404
]:
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
    body: PostDomainsSettingsDomainIdBody | Unset = UNSET,
) -> Response[
    PostDomainsSettingsDomainIdResponse200
    | PostDomainsSettingsDomainIdResponse400
    | PostDomainsSettingsDomainIdResponse401
    | PostDomainsSettingsDomainIdResponse402
    | PostDomainsSettingsDomainIdResponse403
    | PostDomainsSettingsDomainIdResponse404
]:
    """Update domain settings

     Update domain settings

    Args:
        domain_id (int):
        body (PostDomainsSettingsDomainIdBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostDomainsSettingsDomainIdResponse200 | PostDomainsSettingsDomainIdResponse400 | PostDomainsSettingsDomainIdResponse401 | PostDomainsSettingsDomainIdResponse402 | PostDomainsSettingsDomainIdResponse403 | PostDomainsSettingsDomainIdResponse404]
    """

    kwargs = _get_kwargs(
        domain_id=domain_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    domain_id: int,
    *,
    client: AuthenticatedClient | Client,
    body: PostDomainsSettingsDomainIdBody | Unset = UNSET,
) -> (
    PostDomainsSettingsDomainIdResponse200
    | PostDomainsSettingsDomainIdResponse400
    | PostDomainsSettingsDomainIdResponse401
    | PostDomainsSettingsDomainIdResponse402
    | PostDomainsSettingsDomainIdResponse403
    | PostDomainsSettingsDomainIdResponse404
    | None
):
    """Update domain settings

     Update domain settings

    Args:
        domain_id (int):
        body (PostDomainsSettingsDomainIdBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostDomainsSettingsDomainIdResponse200 | PostDomainsSettingsDomainIdResponse400 | PostDomainsSettingsDomainIdResponse401 | PostDomainsSettingsDomainIdResponse402 | PostDomainsSettingsDomainIdResponse403 | PostDomainsSettingsDomainIdResponse404
    """

    return sync_detailed(
        domain_id=domain_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    domain_id: int,
    *,
    client: AuthenticatedClient | Client,
    body: PostDomainsSettingsDomainIdBody | Unset = UNSET,
) -> Response[
    PostDomainsSettingsDomainIdResponse200
    | PostDomainsSettingsDomainIdResponse400
    | PostDomainsSettingsDomainIdResponse401
    | PostDomainsSettingsDomainIdResponse402
    | PostDomainsSettingsDomainIdResponse403
    | PostDomainsSettingsDomainIdResponse404
]:
    """Update domain settings

     Update domain settings

    Args:
        domain_id (int):
        body (PostDomainsSettingsDomainIdBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostDomainsSettingsDomainIdResponse200 | PostDomainsSettingsDomainIdResponse400 | PostDomainsSettingsDomainIdResponse401 | PostDomainsSettingsDomainIdResponse402 | PostDomainsSettingsDomainIdResponse403 | PostDomainsSettingsDomainIdResponse404]
    """

    kwargs = _get_kwargs(
        domain_id=domain_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    domain_id: int,
    *,
    client: AuthenticatedClient | Client,
    body: PostDomainsSettingsDomainIdBody | Unset = UNSET,
) -> (
    PostDomainsSettingsDomainIdResponse200
    | PostDomainsSettingsDomainIdResponse400
    | PostDomainsSettingsDomainIdResponse401
    | PostDomainsSettingsDomainIdResponse402
    | PostDomainsSettingsDomainIdResponse403
    | PostDomainsSettingsDomainIdResponse404
    | None
):
    """Update domain settings

     Update domain settings

    Args:
        domain_id (int):
        body (PostDomainsSettingsDomainIdBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostDomainsSettingsDomainIdResponse200 | PostDomainsSettingsDomainIdResponse400 | PostDomainsSettingsDomainIdResponse401 | PostDomainsSettingsDomainIdResponse402 | PostDomainsSettingsDomainIdResponse403 | PostDomainsSettingsDomainIdResponse404
    """

    return (
        await asyncio_detailed(
            domain_id=domain_id,
            client=client,
            body=body,
        )
    ).parsed
