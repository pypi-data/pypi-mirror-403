from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_links_examples_body import PostLinksExamplesBody
from ...models.post_links_examples_response_200 import PostLinksExamplesResponse200
from ...models.post_links_examples_response_400 import PostLinksExamplesResponse400
from ...models.post_links_examples_response_401 import PostLinksExamplesResponse401
from ...models.post_links_examples_response_402 import PostLinksExamplesResponse402
from ...models.post_links_examples_response_403 import PostLinksExamplesResponse403
from ...models.post_links_examples_response_404 import PostLinksExamplesResponse404
from ...models.post_links_examples_response_409 import PostLinksExamplesResponse409
from ...models.post_links_examples_response_500 import PostLinksExamplesResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: PostLinksExamplesBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/links/examples",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    PostLinksExamplesResponse200
    | PostLinksExamplesResponse400
    | PostLinksExamplesResponse401
    | PostLinksExamplesResponse402
    | PostLinksExamplesResponse403
    | PostLinksExamplesResponse404
    | PostLinksExamplesResponse409
    | PostLinksExamplesResponse500
    | None
):
    if response.status_code == 200:
        response_200 = PostLinksExamplesResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = PostLinksExamplesResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = PostLinksExamplesResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 402:
        response_402 = PostLinksExamplesResponse402.from_dict(response.json())

        return response_402

    if response.status_code == 403:
        response_403 = PostLinksExamplesResponse403.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = PostLinksExamplesResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = PostLinksExamplesResponse409.from_dict(response.json())

        return response_409

    if response.status_code == 500:
        response_500 = PostLinksExamplesResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    PostLinksExamplesResponse200
    | PostLinksExamplesResponse400
    | PostLinksExamplesResponse401
    | PostLinksExamplesResponse402
    | PostLinksExamplesResponse403
    | PostLinksExamplesResponse404
    | PostLinksExamplesResponse409
    | PostLinksExamplesResponse500
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
    body: PostLinksExamplesBody,
) -> Response[
    PostLinksExamplesResponse200
    | PostLinksExamplesResponse400
    | PostLinksExamplesResponse401
    | PostLinksExamplesResponse402
    | PostLinksExamplesResponse403
    | PostLinksExamplesResponse404
    | PostLinksExamplesResponse409
    | PostLinksExamplesResponse500
]:
    """Generate example links for a domain

     Creates a set of demo/example links to showcase various features of the short link service.

    Example links include:
    - A/B testing with split URLs
    - Mobile targeting (different URLs for Android/iPhone)
    - Expiring links with time limits
    - File download links
    - Password-protected links

    **Rate limit**: 5/10s

    Args:
        body (PostLinksExamplesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostLinksExamplesResponse200 | PostLinksExamplesResponse400 | PostLinksExamplesResponse401 | PostLinksExamplesResponse402 | PostLinksExamplesResponse403 | PostLinksExamplesResponse404 | PostLinksExamplesResponse409 | PostLinksExamplesResponse500]
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
    body: PostLinksExamplesBody,
) -> (
    PostLinksExamplesResponse200
    | PostLinksExamplesResponse400
    | PostLinksExamplesResponse401
    | PostLinksExamplesResponse402
    | PostLinksExamplesResponse403
    | PostLinksExamplesResponse404
    | PostLinksExamplesResponse409
    | PostLinksExamplesResponse500
    | None
):
    """Generate example links for a domain

     Creates a set of demo/example links to showcase various features of the short link service.

    Example links include:
    - A/B testing with split URLs
    - Mobile targeting (different URLs for Android/iPhone)
    - Expiring links with time limits
    - File download links
    - Password-protected links

    **Rate limit**: 5/10s

    Args:
        body (PostLinksExamplesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostLinksExamplesResponse200 | PostLinksExamplesResponse400 | PostLinksExamplesResponse401 | PostLinksExamplesResponse402 | PostLinksExamplesResponse403 | PostLinksExamplesResponse404 | PostLinksExamplesResponse409 | PostLinksExamplesResponse500
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksExamplesBody,
) -> Response[
    PostLinksExamplesResponse200
    | PostLinksExamplesResponse400
    | PostLinksExamplesResponse401
    | PostLinksExamplesResponse402
    | PostLinksExamplesResponse403
    | PostLinksExamplesResponse404
    | PostLinksExamplesResponse409
    | PostLinksExamplesResponse500
]:
    """Generate example links for a domain

     Creates a set of demo/example links to showcase various features of the short link service.

    Example links include:
    - A/B testing with split URLs
    - Mobile targeting (different URLs for Android/iPhone)
    - Expiring links with time limits
    - File download links
    - Password-protected links

    **Rate limit**: 5/10s

    Args:
        body (PostLinksExamplesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostLinksExamplesResponse200 | PostLinksExamplesResponse400 | PostLinksExamplesResponse401 | PostLinksExamplesResponse402 | PostLinksExamplesResponse403 | PostLinksExamplesResponse404 | PostLinksExamplesResponse409 | PostLinksExamplesResponse500]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksExamplesBody,
) -> (
    PostLinksExamplesResponse200
    | PostLinksExamplesResponse400
    | PostLinksExamplesResponse401
    | PostLinksExamplesResponse402
    | PostLinksExamplesResponse403
    | PostLinksExamplesResponse404
    | PostLinksExamplesResponse409
    | PostLinksExamplesResponse500
    | None
):
    """Generate example links for a domain

     Creates a set of demo/example links to showcase various features of the short link service.

    Example links include:
    - A/B testing with split URLs
    - Mobile targeting (different URLs for Android/iPhone)
    - Expiring links with time limits
    - File download links
    - Password-protected links

    **Rate limit**: 5/10s

    Args:
        body (PostLinksExamplesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostLinksExamplesResponse200 | PostLinksExamplesResponse400 | PostLinksExamplesResponse401 | PostLinksExamplesResponse402 | PostLinksExamplesResponse403 | PostLinksExamplesResponse404 | PostLinksExamplesResponse409 | PostLinksExamplesResponse500
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
