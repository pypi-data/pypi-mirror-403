from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_links_archive_bulk_body import PostLinksArchiveBulkBody
from ...models.post_links_archive_bulk_response_200 import PostLinksArchiveBulkResponse200
from ...models.post_links_archive_bulk_response_400 import PostLinksArchiveBulkResponse400
from ...models.post_links_archive_bulk_response_401 import PostLinksArchiveBulkResponse401
from ...models.post_links_archive_bulk_response_402 import PostLinksArchiveBulkResponse402
from ...models.post_links_archive_bulk_response_403 import PostLinksArchiveBulkResponse403
from ...models.post_links_archive_bulk_response_404 import PostLinksArchiveBulkResponse404
from ...models.post_links_archive_bulk_response_409 import PostLinksArchiveBulkResponse409
from ...models.post_links_archive_bulk_response_500 import PostLinksArchiveBulkResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: PostLinksArchiveBulkBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/links/archive_bulk",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    PostLinksArchiveBulkResponse200
    | PostLinksArchiveBulkResponse400
    | PostLinksArchiveBulkResponse401
    | PostLinksArchiveBulkResponse402
    | PostLinksArchiveBulkResponse403
    | PostLinksArchiveBulkResponse404
    | PostLinksArchiveBulkResponse409
    | PostLinksArchiveBulkResponse500
    | None
):
    if response.status_code == 200:
        response_200 = PostLinksArchiveBulkResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = PostLinksArchiveBulkResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = PostLinksArchiveBulkResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 402:
        response_402 = PostLinksArchiveBulkResponse402.from_dict(response.json())

        return response_402

    if response.status_code == 403:
        response_403 = PostLinksArchiveBulkResponse403.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = PostLinksArchiveBulkResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = PostLinksArchiveBulkResponse409.from_dict(response.json())

        return response_409

    if response.status_code == 500:
        response_500 = PostLinksArchiveBulkResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    PostLinksArchiveBulkResponse200
    | PostLinksArchiveBulkResponse400
    | PostLinksArchiveBulkResponse401
    | PostLinksArchiveBulkResponse402
    | PostLinksArchiveBulkResponse403
    | PostLinksArchiveBulkResponse404
    | PostLinksArchiveBulkResponse409
    | PostLinksArchiveBulkResponse500
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
    body: PostLinksArchiveBulkBody,
) -> Response[
    PostLinksArchiveBulkResponse200
    | PostLinksArchiveBulkResponse400
    | PostLinksArchiveBulkResponse401
    | PostLinksArchiveBulkResponse402
    | PostLinksArchiveBulkResponse403
    | PostLinksArchiveBulkResponse404
    | PostLinksArchiveBulkResponse409
    | PostLinksArchiveBulkResponse500
]:
    """Archive links in bulk

    Args:
        body (PostLinksArchiveBulkBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostLinksArchiveBulkResponse200 | PostLinksArchiveBulkResponse400 | PostLinksArchiveBulkResponse401 | PostLinksArchiveBulkResponse402 | PostLinksArchiveBulkResponse403 | PostLinksArchiveBulkResponse404 | PostLinksArchiveBulkResponse409 | PostLinksArchiveBulkResponse500]
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
    body: PostLinksArchiveBulkBody,
) -> (
    PostLinksArchiveBulkResponse200
    | PostLinksArchiveBulkResponse400
    | PostLinksArchiveBulkResponse401
    | PostLinksArchiveBulkResponse402
    | PostLinksArchiveBulkResponse403
    | PostLinksArchiveBulkResponse404
    | PostLinksArchiveBulkResponse409
    | PostLinksArchiveBulkResponse500
    | None
):
    """Archive links in bulk

    Args:
        body (PostLinksArchiveBulkBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostLinksArchiveBulkResponse200 | PostLinksArchiveBulkResponse400 | PostLinksArchiveBulkResponse401 | PostLinksArchiveBulkResponse402 | PostLinksArchiveBulkResponse403 | PostLinksArchiveBulkResponse404 | PostLinksArchiveBulkResponse409 | PostLinksArchiveBulkResponse500
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksArchiveBulkBody,
) -> Response[
    PostLinksArchiveBulkResponse200
    | PostLinksArchiveBulkResponse400
    | PostLinksArchiveBulkResponse401
    | PostLinksArchiveBulkResponse402
    | PostLinksArchiveBulkResponse403
    | PostLinksArchiveBulkResponse404
    | PostLinksArchiveBulkResponse409
    | PostLinksArchiveBulkResponse500
]:
    """Archive links in bulk

    Args:
        body (PostLinksArchiveBulkBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostLinksArchiveBulkResponse200 | PostLinksArchiveBulkResponse400 | PostLinksArchiveBulkResponse401 | PostLinksArchiveBulkResponse402 | PostLinksArchiveBulkResponse403 | PostLinksArchiveBulkResponse404 | PostLinksArchiveBulkResponse409 | PostLinksArchiveBulkResponse500]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksArchiveBulkBody,
) -> (
    PostLinksArchiveBulkResponse200
    | PostLinksArchiveBulkResponse400
    | PostLinksArchiveBulkResponse401
    | PostLinksArchiveBulkResponse402
    | PostLinksArchiveBulkResponse403
    | PostLinksArchiveBulkResponse404
    | PostLinksArchiveBulkResponse409
    | PostLinksArchiveBulkResponse500
    | None
):
    """Archive links in bulk

    Args:
        body (PostLinksArchiveBulkBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostLinksArchiveBulkResponse200 | PostLinksArchiveBulkResponse400 | PostLinksArchiveBulkResponse401 | PostLinksArchiveBulkResponse402 | PostLinksArchiveBulkResponse403 | PostLinksArchiveBulkResponse404 | PostLinksArchiveBulkResponse409 | PostLinksArchiveBulkResponse500
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
