from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_domains_body import PostDomainsBody
from ...models.post_domains_response_200 import PostDomainsResponse200
from ...models.post_domains_response_402 import PostDomainsResponse402
from ...models.post_domains_response_403 import PostDomainsResponse403
from ...models.post_domains_response_409 import PostDomainsResponse409
from ...types import Response


def _get_kwargs(
    *,
    body: PostDomainsBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/domains",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> PostDomainsResponse200 | PostDomainsResponse402 | PostDomainsResponse403 | PostDomainsResponse409 | None:
    if response.status_code == 200:
        response_200 = PostDomainsResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 402:
        response_402 = PostDomainsResponse402.from_dict(response.json())

        return response_402

    if response.status_code == 403:
        response_403 = PostDomainsResponse403.from_dict(response.json())

        return response_403

    if response.status_code == 409:
        response_409 = PostDomainsResponse409.from_dict(response.json())

        return response_409

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[PostDomainsResponse200 | PostDomainsResponse402 | PostDomainsResponse403 | PostDomainsResponse409]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostDomainsBody,
) -> Response[PostDomainsResponse200 | PostDomainsResponse402 | PostDomainsResponse403 | PostDomainsResponse409]:
    """Create a domain

    Args:
        body (PostDomainsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostDomainsResponse200 | PostDomainsResponse402 | PostDomainsResponse403 | PostDomainsResponse409]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: PostDomainsBody,
) -> PostDomainsResponse200 | PostDomainsResponse402 | PostDomainsResponse403 | PostDomainsResponse409 | None:
    """Create a domain

    Args:
        body (PostDomainsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostDomainsResponse200 | PostDomainsResponse402 | PostDomainsResponse403 | PostDomainsResponse409
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostDomainsBody,
) -> Response[PostDomainsResponse200 | PostDomainsResponse402 | PostDomainsResponse403 | PostDomainsResponse409]:
    """Create a domain

    Args:
        body (PostDomainsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostDomainsResponse200 | PostDomainsResponse402 | PostDomainsResponse403 | PostDomainsResponse409]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: PostDomainsBody,
) -> PostDomainsResponse200 | PostDomainsResponse402 | PostDomainsResponse403 | PostDomainsResponse409 | None:
    """Create a domain

    Args:
        body (PostDomainsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostDomainsResponse200 | PostDomainsResponse402 | PostDomainsResponse403 | PostDomainsResponse409
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
