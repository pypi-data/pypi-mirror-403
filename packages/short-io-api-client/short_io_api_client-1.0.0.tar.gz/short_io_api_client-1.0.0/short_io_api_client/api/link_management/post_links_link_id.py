from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_links_link_id_body import PostLinksLinkIdBody
from ...models.post_links_link_id_response_200 import PostLinksLinkIdResponse200
from ...models.post_links_link_id_response_400 import PostLinksLinkIdResponse400
from ...models.post_links_link_id_response_401 import PostLinksLinkIdResponse401
from ...models.post_links_link_id_response_402 import PostLinksLinkIdResponse402
from ...models.post_links_link_id_response_403 import PostLinksLinkIdResponse403
from ...models.post_links_link_id_response_404 import PostLinksLinkIdResponse404
from ...models.post_links_link_id_response_409 import PostLinksLinkIdResponse409
from ...models.post_links_link_id_response_500 import PostLinksLinkIdResponse500
from ...types import UNSET, Response, Unset


def _get_kwargs(
    link_id: str,
    *,
    body: PostLinksLinkIdBody | Unset = UNSET,
    domain_id: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["domain_id"] = domain_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/links/{link_id}".format(
            link_id=quote(str(link_id), safe=""),
        ),
        "params": params,
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    PostLinksLinkIdResponse200
    | PostLinksLinkIdResponse400
    | PostLinksLinkIdResponse401
    | PostLinksLinkIdResponse402
    | PostLinksLinkIdResponse403
    | PostLinksLinkIdResponse404
    | PostLinksLinkIdResponse409
    | PostLinksLinkIdResponse500
    | None
):
    if response.status_code == 200:
        response_200 = PostLinksLinkIdResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = PostLinksLinkIdResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = PostLinksLinkIdResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 402:
        response_402 = PostLinksLinkIdResponse402.from_dict(response.json())

        return response_402

    if response.status_code == 403:
        response_403 = PostLinksLinkIdResponse403.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = PostLinksLinkIdResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = PostLinksLinkIdResponse409.from_dict(response.json())

        return response_409

    if response.status_code == 500:
        response_500 = PostLinksLinkIdResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    PostLinksLinkIdResponse200
    | PostLinksLinkIdResponse400
    | PostLinksLinkIdResponse401
    | PostLinksLinkIdResponse402
    | PostLinksLinkIdResponse403
    | PostLinksLinkIdResponse404
    | PostLinksLinkIdResponse409
    | PostLinksLinkIdResponse500
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
    body: PostLinksLinkIdBody | Unset = UNSET,
    domain_id: str | Unset = UNSET,
) -> Response[
    PostLinksLinkIdResponse200
    | PostLinksLinkIdResponse400
    | PostLinksLinkIdResponse401
    | PostLinksLinkIdResponse402
    | PostLinksLinkIdResponse403
    | PostLinksLinkIdResponse404
    | PostLinksLinkIdResponse409
    | PostLinksLinkIdResponse500
]:
    """Update existing URL

     Update original url, title or path for existing URL by id

    **Rate limit**: 20/s

    Args:
        link_id (str):
        domain_id (str | Unset):
        body (PostLinksLinkIdBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostLinksLinkIdResponse200 | PostLinksLinkIdResponse400 | PostLinksLinkIdResponse401 | PostLinksLinkIdResponse402 | PostLinksLinkIdResponse403 | PostLinksLinkIdResponse404 | PostLinksLinkIdResponse409 | PostLinksLinkIdResponse500]
    """

    kwargs = _get_kwargs(
        link_id=link_id,
        body=body,
        domain_id=domain_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksLinkIdBody | Unset = UNSET,
    domain_id: str | Unset = UNSET,
) -> (
    PostLinksLinkIdResponse200
    | PostLinksLinkIdResponse400
    | PostLinksLinkIdResponse401
    | PostLinksLinkIdResponse402
    | PostLinksLinkIdResponse403
    | PostLinksLinkIdResponse404
    | PostLinksLinkIdResponse409
    | PostLinksLinkIdResponse500
    | None
):
    """Update existing URL

     Update original url, title or path for existing URL by id

    **Rate limit**: 20/s

    Args:
        link_id (str):
        domain_id (str | Unset):
        body (PostLinksLinkIdBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostLinksLinkIdResponse200 | PostLinksLinkIdResponse400 | PostLinksLinkIdResponse401 | PostLinksLinkIdResponse402 | PostLinksLinkIdResponse403 | PostLinksLinkIdResponse404 | PostLinksLinkIdResponse409 | PostLinksLinkIdResponse500
    """

    return sync_detailed(
        link_id=link_id,
        client=client,
        body=body,
        domain_id=domain_id,
    ).parsed


async def asyncio_detailed(
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksLinkIdBody | Unset = UNSET,
    domain_id: str | Unset = UNSET,
) -> Response[
    PostLinksLinkIdResponse200
    | PostLinksLinkIdResponse400
    | PostLinksLinkIdResponse401
    | PostLinksLinkIdResponse402
    | PostLinksLinkIdResponse403
    | PostLinksLinkIdResponse404
    | PostLinksLinkIdResponse409
    | PostLinksLinkIdResponse500
]:
    """Update existing URL

     Update original url, title or path for existing URL by id

    **Rate limit**: 20/s

    Args:
        link_id (str):
        domain_id (str | Unset):
        body (PostLinksLinkIdBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostLinksLinkIdResponse200 | PostLinksLinkIdResponse400 | PostLinksLinkIdResponse401 | PostLinksLinkIdResponse402 | PostLinksLinkIdResponse403 | PostLinksLinkIdResponse404 | PostLinksLinkIdResponse409 | PostLinksLinkIdResponse500]
    """

    kwargs = _get_kwargs(
        link_id=link_id,
        body=body,
        domain_id=domain_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksLinkIdBody | Unset = UNSET,
    domain_id: str | Unset = UNSET,
) -> (
    PostLinksLinkIdResponse200
    | PostLinksLinkIdResponse400
    | PostLinksLinkIdResponse401
    | PostLinksLinkIdResponse402
    | PostLinksLinkIdResponse403
    | PostLinksLinkIdResponse404
    | PostLinksLinkIdResponse409
    | PostLinksLinkIdResponse500
    | None
):
    """Update existing URL

     Update original url, title or path for existing URL by id

    **Rate limit**: 20/s

    Args:
        link_id (str):
        domain_id (str | Unset):
        body (PostLinksLinkIdBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostLinksLinkIdResponse200 | PostLinksLinkIdResponse400 | PostLinksLinkIdResponse401 | PostLinksLinkIdResponse402 | PostLinksLinkIdResponse403 | PostLinksLinkIdResponse404 | PostLinksLinkIdResponse409 | PostLinksLinkIdResponse500
    """

    return (
        await asyncio_detailed(
            link_id=link_id,
            client=client,
            body=body,
            domain_id=domain_id,
        )
    ).parsed
