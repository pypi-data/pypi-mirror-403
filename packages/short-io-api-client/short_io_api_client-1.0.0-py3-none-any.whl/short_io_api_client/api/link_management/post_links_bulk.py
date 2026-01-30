from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_links_bulk_body import PostLinksBulkBody
from ...types import Response


def _get_kwargs(
    *,
    body: PostLinksBulkBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/links/bulk",
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
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksBulkBody,
) -> Response[Any]:
    """Create up to 1000 links in one call

     Please use this method if you need to create big packs of links. It
    accepts up to 1000 links in one API call.

    It works almost the same as single link creation endpoint, but accepts
    an array of URLs and returns an array of responses.

    Returns list of Link objects. If any URL is failed to insert, it returns
    error object instead as array element. Method is not transactional – it
    can insert some links from the list and return an error for others.

    **Rate limit**: 5 queries in 10 seconds

    Args:
        body (PostLinksBulkBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksBulkBody,
) -> Response[Any]:
    """Create up to 1000 links in one call

     Please use this method if you need to create big packs of links. It
    accepts up to 1000 links in one API call.

    It works almost the same as single link creation endpoint, but accepts
    an array of URLs and returns an array of responses.

    Returns list of Link objects. If any URL is failed to insert, it returns
    error object instead as array element. Method is not transactional – it
    can insert some links from the list and return an error for others.

    **Rate limit**: 5 queries in 10 seconds

    Args:
        body (PostLinksBulkBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)
