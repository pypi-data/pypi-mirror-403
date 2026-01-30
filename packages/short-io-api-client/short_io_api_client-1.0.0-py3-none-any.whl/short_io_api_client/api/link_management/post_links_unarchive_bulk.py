from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_links_unarchive_bulk_body import PostLinksUnarchiveBulkBody
from ...models.post_links_unarchive_bulk_response_200 import PostLinksUnarchiveBulkResponse200
from ...models.post_links_unarchive_bulk_response_400 import PostLinksUnarchiveBulkResponse400
from ...models.post_links_unarchive_bulk_response_401 import PostLinksUnarchiveBulkResponse401
from ...models.post_links_unarchive_bulk_response_402 import PostLinksUnarchiveBulkResponse402
from ...models.post_links_unarchive_bulk_response_403 import PostLinksUnarchiveBulkResponse403
from ...models.post_links_unarchive_bulk_response_404 import PostLinksUnarchiveBulkResponse404
from ...models.post_links_unarchive_bulk_response_409 import PostLinksUnarchiveBulkResponse409
from ...models.post_links_unarchive_bulk_response_500 import PostLinksUnarchiveBulkResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: PostLinksUnarchiveBulkBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/links/unarchive_bulk",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    PostLinksUnarchiveBulkResponse200
    | PostLinksUnarchiveBulkResponse400
    | PostLinksUnarchiveBulkResponse401
    | PostLinksUnarchiveBulkResponse402
    | PostLinksUnarchiveBulkResponse403
    | PostLinksUnarchiveBulkResponse404
    | PostLinksUnarchiveBulkResponse409
    | PostLinksUnarchiveBulkResponse500
    | None
):
    if response.status_code == 200:
        response_200 = PostLinksUnarchiveBulkResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = PostLinksUnarchiveBulkResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = PostLinksUnarchiveBulkResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 402:
        response_402 = PostLinksUnarchiveBulkResponse402.from_dict(response.json())

        return response_402

    if response.status_code == 403:
        response_403 = PostLinksUnarchiveBulkResponse403.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = PostLinksUnarchiveBulkResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = PostLinksUnarchiveBulkResponse409.from_dict(response.json())

        return response_409

    if response.status_code == 500:
        response_500 = PostLinksUnarchiveBulkResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    PostLinksUnarchiveBulkResponse200
    | PostLinksUnarchiveBulkResponse400
    | PostLinksUnarchiveBulkResponse401
    | PostLinksUnarchiveBulkResponse402
    | PostLinksUnarchiveBulkResponse403
    | PostLinksUnarchiveBulkResponse404
    | PostLinksUnarchiveBulkResponse409
    | PostLinksUnarchiveBulkResponse500
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksUnarchiveBulkBody,
) -> Response[
    PostLinksUnarchiveBulkResponse200
    | PostLinksUnarchiveBulkResponse400
    | PostLinksUnarchiveBulkResponse401
    | PostLinksUnarchiveBulkResponse402
    | PostLinksUnarchiveBulkResponse403
    | PostLinksUnarchiveBulkResponse404
    | PostLinksUnarchiveBulkResponse409
    | PostLinksUnarchiveBulkResponse500
]:
    """Unarchive links in bulk

    Args:
        body (PostLinksUnarchiveBulkBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostLinksUnarchiveBulkResponse200 | PostLinksUnarchiveBulkResponse400 | PostLinksUnarchiveBulkResponse401 | PostLinksUnarchiveBulkResponse402 | PostLinksUnarchiveBulkResponse403 | PostLinksUnarchiveBulkResponse404 | PostLinksUnarchiveBulkResponse409 | PostLinksUnarchiveBulkResponse500]
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
    body: PostLinksUnarchiveBulkBody,
) -> (
    PostLinksUnarchiveBulkResponse200
    | PostLinksUnarchiveBulkResponse400
    | PostLinksUnarchiveBulkResponse401
    | PostLinksUnarchiveBulkResponse402
    | PostLinksUnarchiveBulkResponse403
    | PostLinksUnarchiveBulkResponse404
    | PostLinksUnarchiveBulkResponse409
    | PostLinksUnarchiveBulkResponse500
    | None
):
    """Unarchive links in bulk

    Args:
        body (PostLinksUnarchiveBulkBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostLinksUnarchiveBulkResponse200 | PostLinksUnarchiveBulkResponse400 | PostLinksUnarchiveBulkResponse401 | PostLinksUnarchiveBulkResponse402 | PostLinksUnarchiveBulkResponse403 | PostLinksUnarchiveBulkResponse404 | PostLinksUnarchiveBulkResponse409 | PostLinksUnarchiveBulkResponse500
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksUnarchiveBulkBody,
) -> Response[
    PostLinksUnarchiveBulkResponse200
    | PostLinksUnarchiveBulkResponse400
    | PostLinksUnarchiveBulkResponse401
    | PostLinksUnarchiveBulkResponse402
    | PostLinksUnarchiveBulkResponse403
    | PostLinksUnarchiveBulkResponse404
    | PostLinksUnarchiveBulkResponse409
    | PostLinksUnarchiveBulkResponse500
]:
    """Unarchive links in bulk

    Args:
        body (PostLinksUnarchiveBulkBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostLinksUnarchiveBulkResponse200 | PostLinksUnarchiveBulkResponse400 | PostLinksUnarchiveBulkResponse401 | PostLinksUnarchiveBulkResponse402 | PostLinksUnarchiveBulkResponse403 | PostLinksUnarchiveBulkResponse404 | PostLinksUnarchiveBulkResponse409 | PostLinksUnarchiveBulkResponse500]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksUnarchiveBulkBody,
) -> (
    PostLinksUnarchiveBulkResponse200
    | PostLinksUnarchiveBulkResponse400
    | PostLinksUnarchiveBulkResponse401
    | PostLinksUnarchiveBulkResponse402
    | PostLinksUnarchiveBulkResponse403
    | PostLinksUnarchiveBulkResponse404
    | PostLinksUnarchiveBulkResponse409
    | PostLinksUnarchiveBulkResponse500
    | None
):
    """Unarchive links in bulk

    Args:
        body (PostLinksUnarchiveBulkBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostLinksUnarchiveBulkResponse200 | PostLinksUnarchiveBulkResponse400 | PostLinksUnarchiveBulkResponse401 | PostLinksUnarchiveBulkResponse402 | PostLinksUnarchiveBulkResponse403 | PostLinksUnarchiveBulkResponse404 | PostLinksUnarchiveBulkResponse409 | PostLinksUnarchiveBulkResponse500
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
