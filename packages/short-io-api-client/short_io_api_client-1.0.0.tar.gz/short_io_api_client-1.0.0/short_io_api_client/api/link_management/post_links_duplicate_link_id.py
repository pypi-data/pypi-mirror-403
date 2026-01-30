from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_links_duplicate_link_id_body import PostLinksDuplicateLinkIdBody
from ...models.post_links_duplicate_link_id_response_200 import PostLinksDuplicateLinkIdResponse200
from ...models.post_links_duplicate_link_id_response_400 import PostLinksDuplicateLinkIdResponse400
from ...models.post_links_duplicate_link_id_response_401 import PostLinksDuplicateLinkIdResponse401
from ...models.post_links_duplicate_link_id_response_402 import PostLinksDuplicateLinkIdResponse402
from ...models.post_links_duplicate_link_id_response_403 import PostLinksDuplicateLinkIdResponse403
from ...models.post_links_duplicate_link_id_response_404 import PostLinksDuplicateLinkIdResponse404
from ...models.post_links_duplicate_link_id_response_409 import PostLinksDuplicateLinkIdResponse409
from ...models.post_links_duplicate_link_id_response_500 import PostLinksDuplicateLinkIdResponse500
from ...types import UNSET, Response, Unset


def _get_kwargs(
    link_id: str,
    *,
    body: PostLinksDuplicateLinkIdBody | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/links/duplicate/{link_id}".format(
            link_id=quote(str(link_id), safe=""),
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
    PostLinksDuplicateLinkIdResponse200
    | PostLinksDuplicateLinkIdResponse400
    | PostLinksDuplicateLinkIdResponse401
    | PostLinksDuplicateLinkIdResponse402
    | PostLinksDuplicateLinkIdResponse403
    | PostLinksDuplicateLinkIdResponse404
    | PostLinksDuplicateLinkIdResponse409
    | PostLinksDuplicateLinkIdResponse500
    | None
):
    if response.status_code == 200:
        response_200 = PostLinksDuplicateLinkIdResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = PostLinksDuplicateLinkIdResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = PostLinksDuplicateLinkIdResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 402:
        response_402 = PostLinksDuplicateLinkIdResponse402.from_dict(response.json())

        return response_402

    if response.status_code == 403:
        response_403 = PostLinksDuplicateLinkIdResponse403.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = PostLinksDuplicateLinkIdResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = PostLinksDuplicateLinkIdResponse409.from_dict(response.json())

        return response_409

    if response.status_code == 500:
        response_500 = PostLinksDuplicateLinkIdResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    PostLinksDuplicateLinkIdResponse200
    | PostLinksDuplicateLinkIdResponse400
    | PostLinksDuplicateLinkIdResponse401
    | PostLinksDuplicateLinkIdResponse402
    | PostLinksDuplicateLinkIdResponse403
    | PostLinksDuplicateLinkIdResponse404
    | PostLinksDuplicateLinkIdResponse409
    | PostLinksDuplicateLinkIdResponse500
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksDuplicateLinkIdBody | Unset = UNSET,
) -> Response[
    PostLinksDuplicateLinkIdResponse200
    | PostLinksDuplicateLinkIdResponse400
    | PostLinksDuplicateLinkIdResponse401
    | PostLinksDuplicateLinkIdResponse402
    | PostLinksDuplicateLinkIdResponse403
    | PostLinksDuplicateLinkIdResponse404
    | PostLinksDuplicateLinkIdResponse409
    | PostLinksDuplicateLinkIdResponse500
]:
    """Duplicate an existing link

     Duplicates an existing link with all its properties, targeting rules, and settings.
    The duplicated link will have a new random path (or custom if provided) and be fully independent.

    **Rate limit**: 50/s

    Args:
        link_id (str):
        body (PostLinksDuplicateLinkIdBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostLinksDuplicateLinkIdResponse200 | PostLinksDuplicateLinkIdResponse400 | PostLinksDuplicateLinkIdResponse401 | PostLinksDuplicateLinkIdResponse402 | PostLinksDuplicateLinkIdResponse403 | PostLinksDuplicateLinkIdResponse404 | PostLinksDuplicateLinkIdResponse409 | PostLinksDuplicateLinkIdResponse500]
    """

    kwargs = _get_kwargs(
        link_id=link_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksDuplicateLinkIdBody | Unset = UNSET,
) -> (
    PostLinksDuplicateLinkIdResponse200
    | PostLinksDuplicateLinkIdResponse400
    | PostLinksDuplicateLinkIdResponse401
    | PostLinksDuplicateLinkIdResponse402
    | PostLinksDuplicateLinkIdResponse403
    | PostLinksDuplicateLinkIdResponse404
    | PostLinksDuplicateLinkIdResponse409
    | PostLinksDuplicateLinkIdResponse500
    | None
):
    """Duplicate an existing link

     Duplicates an existing link with all its properties, targeting rules, and settings.
    The duplicated link will have a new random path (or custom if provided) and be fully independent.

    **Rate limit**: 50/s

    Args:
        link_id (str):
        body (PostLinksDuplicateLinkIdBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostLinksDuplicateLinkIdResponse200 | PostLinksDuplicateLinkIdResponse400 | PostLinksDuplicateLinkIdResponse401 | PostLinksDuplicateLinkIdResponse402 | PostLinksDuplicateLinkIdResponse403 | PostLinksDuplicateLinkIdResponse404 | PostLinksDuplicateLinkIdResponse409 | PostLinksDuplicateLinkIdResponse500
    """

    return sync_detailed(
        link_id=link_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksDuplicateLinkIdBody | Unset = UNSET,
) -> Response[
    PostLinksDuplicateLinkIdResponse200
    | PostLinksDuplicateLinkIdResponse400
    | PostLinksDuplicateLinkIdResponse401
    | PostLinksDuplicateLinkIdResponse402
    | PostLinksDuplicateLinkIdResponse403
    | PostLinksDuplicateLinkIdResponse404
    | PostLinksDuplicateLinkIdResponse409
    | PostLinksDuplicateLinkIdResponse500
]:
    """Duplicate an existing link

     Duplicates an existing link with all its properties, targeting rules, and settings.
    The duplicated link will have a new random path (or custom if provided) and be fully independent.

    **Rate limit**: 50/s

    Args:
        link_id (str):
        body (PostLinksDuplicateLinkIdBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostLinksDuplicateLinkIdResponse200 | PostLinksDuplicateLinkIdResponse400 | PostLinksDuplicateLinkIdResponse401 | PostLinksDuplicateLinkIdResponse402 | PostLinksDuplicateLinkIdResponse403 | PostLinksDuplicateLinkIdResponse404 | PostLinksDuplicateLinkIdResponse409 | PostLinksDuplicateLinkIdResponse500]
    """

    kwargs = _get_kwargs(
        link_id=link_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksDuplicateLinkIdBody | Unset = UNSET,
) -> (
    PostLinksDuplicateLinkIdResponse200
    | PostLinksDuplicateLinkIdResponse400
    | PostLinksDuplicateLinkIdResponse401
    | PostLinksDuplicateLinkIdResponse402
    | PostLinksDuplicateLinkIdResponse403
    | PostLinksDuplicateLinkIdResponse404
    | PostLinksDuplicateLinkIdResponse409
    | PostLinksDuplicateLinkIdResponse500
    | None
):
    """Duplicate an existing link

     Duplicates an existing link with all its properties, targeting rules, and settings.
    The duplicated link will have a new random path (or custom if provided) and be fully independent.

    **Rate limit**: 50/s

    Args:
        link_id (str):
        body (PostLinksDuplicateLinkIdBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostLinksDuplicateLinkIdResponse200 | PostLinksDuplicateLinkIdResponse400 | PostLinksDuplicateLinkIdResponse401 | PostLinksDuplicateLinkIdResponse402 | PostLinksDuplicateLinkIdResponse403 | PostLinksDuplicateLinkIdResponse404 | PostLinksDuplicateLinkIdResponse409 | PostLinksDuplicateLinkIdResponse500
    """

    return (
        await asyncio_detailed(
            link_id=link_id,
            client=client,
            body=body,
        )
    ).parsed
