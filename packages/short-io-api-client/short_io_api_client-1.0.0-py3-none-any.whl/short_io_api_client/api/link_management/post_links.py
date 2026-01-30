from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_links_body import PostLinksBody
from ...models.post_links_response_200 import PostLinksResponse200
from ...models.post_links_response_400 import PostLinksResponse400
from ...models.post_links_response_401 import PostLinksResponse401
from ...models.post_links_response_402 import PostLinksResponse402
from ...models.post_links_response_403 import PostLinksResponse403
from ...models.post_links_response_404 import PostLinksResponse404
from ...models.post_links_response_409 import PostLinksResponse409
from ...models.post_links_response_500 import PostLinksResponse500
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: PostLinksBody | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/links",
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    PostLinksResponse200
    | PostLinksResponse400
    | PostLinksResponse401
    | PostLinksResponse402
    | PostLinksResponse403
    | PostLinksResponse404
    | PostLinksResponse409
    | PostLinksResponse500
    | None
):
    if response.status_code == 200:
        response_200 = PostLinksResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = PostLinksResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = PostLinksResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 402:
        response_402 = PostLinksResponse402.from_dict(response.json())

        return response_402

    if response.status_code == 403:
        response_403 = PostLinksResponse403.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = PostLinksResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = PostLinksResponse409.from_dict(response.json())

        return response_409

    if response.status_code == 500:
        response_500 = PostLinksResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    PostLinksResponse200
    | PostLinksResponse400
    | PostLinksResponse401
    | PostLinksResponse402
    | PostLinksResponse403
    | PostLinksResponse404
    | PostLinksResponse409
    | PostLinksResponse500
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
    body: PostLinksBody | Unset = UNSET,
) -> Response[
    PostLinksResponse200
    | PostLinksResponse400
    | PostLinksResponse401
    | PostLinksResponse402
    | PostLinksResponse403
    | PostLinksResponse404
    | PostLinksResponse409
    | PostLinksResponse500
]:
    r"""Create a new link

     This method creates a new link. If parameter \"path\" is omitted, it
    generates path by algorithm, chosen in domain settings.

    Notes:

    1. If URL with a given path already exists and originalURL of the URL in database is equal to
    originalURL argument, it returns information about existing URL
    2. If URL with a given path already exists and originalURL is different from originalURL in
    database, it returns error with a status `409`
    3. If URL with a given originalURL exists, and no path is given, it returns information about
    existing URL and does not create anything
    4. If URL with a given originalURL exists, and custom path is given, it creates a new short URL

    **Rate limit**: 50/s

    Args:
        body (PostLinksBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostLinksResponse200 | PostLinksResponse400 | PostLinksResponse401 | PostLinksResponse402 | PostLinksResponse403 | PostLinksResponse404 | PostLinksResponse409 | PostLinksResponse500]
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
    body: PostLinksBody | Unset = UNSET,
) -> (
    PostLinksResponse200
    | PostLinksResponse400
    | PostLinksResponse401
    | PostLinksResponse402
    | PostLinksResponse403
    | PostLinksResponse404
    | PostLinksResponse409
    | PostLinksResponse500
    | None
):
    r"""Create a new link

     This method creates a new link. If parameter \"path\" is omitted, it
    generates path by algorithm, chosen in domain settings.

    Notes:

    1. If URL with a given path already exists and originalURL of the URL in database is equal to
    originalURL argument, it returns information about existing URL
    2. If URL with a given path already exists and originalURL is different from originalURL in
    database, it returns error with a status `409`
    3. If URL with a given originalURL exists, and no path is given, it returns information about
    existing URL and does not create anything
    4. If URL with a given originalURL exists, and custom path is given, it creates a new short URL

    **Rate limit**: 50/s

    Args:
        body (PostLinksBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostLinksResponse200 | PostLinksResponse400 | PostLinksResponse401 | PostLinksResponse402 | PostLinksResponse403 | PostLinksResponse404 | PostLinksResponse409 | PostLinksResponse500
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksBody | Unset = UNSET,
) -> Response[
    PostLinksResponse200
    | PostLinksResponse400
    | PostLinksResponse401
    | PostLinksResponse402
    | PostLinksResponse403
    | PostLinksResponse404
    | PostLinksResponse409
    | PostLinksResponse500
]:
    r"""Create a new link

     This method creates a new link. If parameter \"path\" is omitted, it
    generates path by algorithm, chosen in domain settings.

    Notes:

    1. If URL with a given path already exists and originalURL of the URL in database is equal to
    originalURL argument, it returns information about existing URL
    2. If URL with a given path already exists and originalURL is different from originalURL in
    database, it returns error with a status `409`
    3. If URL with a given originalURL exists, and no path is given, it returns information about
    existing URL and does not create anything
    4. If URL with a given originalURL exists, and custom path is given, it creates a new short URL

    **Rate limit**: 50/s

    Args:
        body (PostLinksBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostLinksResponse200 | PostLinksResponse400 | PostLinksResponse401 | PostLinksResponse402 | PostLinksResponse403 | PostLinksResponse404 | PostLinksResponse409 | PostLinksResponse500]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksBody | Unset = UNSET,
) -> (
    PostLinksResponse200
    | PostLinksResponse400
    | PostLinksResponse401
    | PostLinksResponse402
    | PostLinksResponse403
    | PostLinksResponse404
    | PostLinksResponse409
    | PostLinksResponse500
    | None
):
    r"""Create a new link

     This method creates a new link. If parameter \"path\" is omitted, it
    generates path by algorithm, chosen in domain settings.

    Notes:

    1. If URL with a given path already exists and originalURL of the URL in database is equal to
    originalURL argument, it returns information about existing URL
    2. If URL with a given path already exists and originalURL is different from originalURL in
    database, it returns error with a status `409`
    3. If URL with a given originalURL exists, and no path is given, it returns information about
    existing URL and does not create anything
    4. If URL with a given originalURL exists, and custom path is given, it creates a new short URL

    **Rate limit**: 50/s

    Args:
        body (PostLinksBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostLinksResponse200 | PostLinksResponse400 | PostLinksResponse401 | PostLinksResponse402 | PostLinksResponse403 | PostLinksResponse404 | PostLinksResponse409 | PostLinksResponse500
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
