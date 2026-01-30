from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_links_archive_body import PostLinksArchiveBody
from ...models.post_links_archive_response_200 import PostLinksArchiveResponse200
from ...models.post_links_archive_response_400 import PostLinksArchiveResponse400
from ...models.post_links_archive_response_401 import PostLinksArchiveResponse401
from ...models.post_links_archive_response_402 import PostLinksArchiveResponse402
from ...models.post_links_archive_response_403 import PostLinksArchiveResponse403
from ...models.post_links_archive_response_404 import PostLinksArchiveResponse404
from ...models.post_links_archive_response_409 import PostLinksArchiveResponse409
from ...models.post_links_archive_response_500 import PostLinksArchiveResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: PostLinksArchiveBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/links/archive",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    PostLinksArchiveResponse200
    | PostLinksArchiveResponse400
    | PostLinksArchiveResponse401
    | PostLinksArchiveResponse402
    | PostLinksArchiveResponse403
    | PostLinksArchiveResponse404
    | PostLinksArchiveResponse409
    | PostLinksArchiveResponse500
    | None
):
    if response.status_code == 200:
        response_200 = PostLinksArchiveResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = PostLinksArchiveResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = PostLinksArchiveResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 402:
        response_402 = PostLinksArchiveResponse402.from_dict(response.json())

        return response_402

    if response.status_code == 403:
        response_403 = PostLinksArchiveResponse403.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = PostLinksArchiveResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = PostLinksArchiveResponse409.from_dict(response.json())

        return response_409

    if response.status_code == 500:
        response_500 = PostLinksArchiveResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    PostLinksArchiveResponse200
    | PostLinksArchiveResponse400
    | PostLinksArchiveResponse401
    | PostLinksArchiveResponse402
    | PostLinksArchiveResponse403
    | PostLinksArchiveResponse404
    | PostLinksArchiveResponse409
    | PostLinksArchiveResponse500
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
    body: PostLinksArchiveBody,
) -> Response[
    PostLinksArchiveResponse200
    | PostLinksArchiveResponse400
    | PostLinksArchiveResponse401
    | PostLinksArchiveResponse402
    | PostLinksArchiveResponse403
    | PostLinksArchiveResponse404
    | PostLinksArchiveResponse409
    | PostLinksArchiveResponse500
]:
    """Archive link

    Args:
        body (PostLinksArchiveBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostLinksArchiveResponse200 | PostLinksArchiveResponse400 | PostLinksArchiveResponse401 | PostLinksArchiveResponse402 | PostLinksArchiveResponse403 | PostLinksArchiveResponse404 | PostLinksArchiveResponse409 | PostLinksArchiveResponse500]
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
    body: PostLinksArchiveBody,
) -> (
    PostLinksArchiveResponse200
    | PostLinksArchiveResponse400
    | PostLinksArchiveResponse401
    | PostLinksArchiveResponse402
    | PostLinksArchiveResponse403
    | PostLinksArchiveResponse404
    | PostLinksArchiveResponse409
    | PostLinksArchiveResponse500
    | None
):
    """Archive link

    Args:
        body (PostLinksArchiveBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostLinksArchiveResponse200 | PostLinksArchiveResponse400 | PostLinksArchiveResponse401 | PostLinksArchiveResponse402 | PostLinksArchiveResponse403 | PostLinksArchiveResponse404 | PostLinksArchiveResponse409 | PostLinksArchiveResponse500
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksArchiveBody,
) -> Response[
    PostLinksArchiveResponse200
    | PostLinksArchiveResponse400
    | PostLinksArchiveResponse401
    | PostLinksArchiveResponse402
    | PostLinksArchiveResponse403
    | PostLinksArchiveResponse404
    | PostLinksArchiveResponse409
    | PostLinksArchiveResponse500
]:
    """Archive link

    Args:
        body (PostLinksArchiveBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostLinksArchiveResponse200 | PostLinksArchiveResponse400 | PostLinksArchiveResponse401 | PostLinksArchiveResponse402 | PostLinksArchiveResponse403 | PostLinksArchiveResponse404 | PostLinksArchiveResponse409 | PostLinksArchiveResponse500]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksArchiveBody,
) -> (
    PostLinksArchiveResponse200
    | PostLinksArchiveResponse400
    | PostLinksArchiveResponse401
    | PostLinksArchiveResponse402
    | PostLinksArchiveResponse403
    | PostLinksArchiveResponse404
    | PostLinksArchiveResponse409
    | PostLinksArchiveResponse500
    | None
):
    """Archive link

    Args:
        body (PostLinksArchiveBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostLinksArchiveResponse200 | PostLinksArchiveResponse400 | PostLinksArchiveResponse401 | PostLinksArchiveResponse402 | PostLinksArchiveResponse403 | PostLinksArchiveResponse404 | PostLinksArchiveResponse409 | PostLinksArchiveResponse500
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
