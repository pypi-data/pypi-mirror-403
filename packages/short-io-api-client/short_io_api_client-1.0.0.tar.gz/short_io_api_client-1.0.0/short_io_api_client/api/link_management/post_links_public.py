from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_links_public_body import PostLinksPublicBody
from ...models.post_links_public_response_200 import PostLinksPublicResponse200
from ...models.post_links_public_response_400 import PostLinksPublicResponse400
from ...models.post_links_public_response_401 import PostLinksPublicResponse401
from ...models.post_links_public_response_402 import PostLinksPublicResponse402
from ...models.post_links_public_response_403 import PostLinksPublicResponse403
from ...models.post_links_public_response_404 import PostLinksPublicResponse404
from ...models.post_links_public_response_409 import PostLinksPublicResponse409
from ...models.post_links_public_response_500 import PostLinksPublicResponse500
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: PostLinksPublicBody,
    type_: str | Unset = UNSET,
    additional_properties: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(type_, Unset):
        headers["type"] = type_

    if not isinstance(additional_properties, Unset):
        headers["additionalProperties"] = additional_properties

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/links/public",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    PostLinksPublicResponse200
    | PostLinksPublicResponse400
    | PostLinksPublicResponse401
    | PostLinksPublicResponse402
    | PostLinksPublicResponse403
    | PostLinksPublicResponse404
    | PostLinksPublicResponse409
    | PostLinksPublicResponse500
    | None
):
    if response.status_code == 200:
        response_200 = PostLinksPublicResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = PostLinksPublicResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = PostLinksPublicResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 402:
        response_402 = PostLinksPublicResponse402.from_dict(response.json())

        return response_402

    if response.status_code == 403:
        response_403 = PostLinksPublicResponse403.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = PostLinksPublicResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = PostLinksPublicResponse409.from_dict(response.json())

        return response_409

    if response.status_code == 500:
        response_500 = PostLinksPublicResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    PostLinksPublicResponse200
    | PostLinksPublicResponse400
    | PostLinksPublicResponse401
    | PostLinksPublicResponse402
    | PostLinksPublicResponse403
    | PostLinksPublicResponse404
    | PostLinksPublicResponse409
    | PostLinksPublicResponse500
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
    body: PostLinksPublicBody,
    type_: str | Unset = UNSET,
    additional_properties: str | Unset = UNSET,
) -> Response[
    PostLinksPublicResponse200
    | PostLinksPublicResponse400
    | PostLinksPublicResponse401
    | PostLinksPublicResponse402
    | PostLinksPublicResponse403
    | PostLinksPublicResponse404
    | PostLinksPublicResponse409
    | PostLinksPublicResponse500
]:
    r"""Create a new link using public API key

     This method creates a new link. Only this method should be used in client-side applications

    If parameter \"path\" is omitted, it generates path by algorithm, chosen in domain settings.

    You can use it with public API key in your frontend applications (client-side javascript, Android &
    iPhone apps)
    **Rate limit**: 50/s

    Args:
        type_ (str | Unset):
        additional_properties (str | Unset):
        body (PostLinksPublicBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostLinksPublicResponse200 | PostLinksPublicResponse400 | PostLinksPublicResponse401 | PostLinksPublicResponse402 | PostLinksPublicResponse403 | PostLinksPublicResponse404 | PostLinksPublicResponse409 | PostLinksPublicResponse500]
    """

    kwargs = _get_kwargs(
        body=body,
        type_=type_,
        additional_properties=additional_properties,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksPublicBody,
    type_: str | Unset = UNSET,
    additional_properties: str | Unset = UNSET,
) -> (
    PostLinksPublicResponse200
    | PostLinksPublicResponse400
    | PostLinksPublicResponse401
    | PostLinksPublicResponse402
    | PostLinksPublicResponse403
    | PostLinksPublicResponse404
    | PostLinksPublicResponse409
    | PostLinksPublicResponse500
    | None
):
    r"""Create a new link using public API key

     This method creates a new link. Only this method should be used in client-side applications

    If parameter \"path\" is omitted, it generates path by algorithm, chosen in domain settings.

    You can use it with public API key in your frontend applications (client-side javascript, Android &
    iPhone apps)
    **Rate limit**: 50/s

    Args:
        type_ (str | Unset):
        additional_properties (str | Unset):
        body (PostLinksPublicBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostLinksPublicResponse200 | PostLinksPublicResponse400 | PostLinksPublicResponse401 | PostLinksPublicResponse402 | PostLinksPublicResponse403 | PostLinksPublicResponse404 | PostLinksPublicResponse409 | PostLinksPublicResponse500
    """

    return sync_detailed(
        client=client,
        body=body,
        type_=type_,
        additional_properties=additional_properties,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksPublicBody,
    type_: str | Unset = UNSET,
    additional_properties: str | Unset = UNSET,
) -> Response[
    PostLinksPublicResponse200
    | PostLinksPublicResponse400
    | PostLinksPublicResponse401
    | PostLinksPublicResponse402
    | PostLinksPublicResponse403
    | PostLinksPublicResponse404
    | PostLinksPublicResponse409
    | PostLinksPublicResponse500
]:
    r"""Create a new link using public API key

     This method creates a new link. Only this method should be used in client-side applications

    If parameter \"path\" is omitted, it generates path by algorithm, chosen in domain settings.

    You can use it with public API key in your frontend applications (client-side javascript, Android &
    iPhone apps)
    **Rate limit**: 50/s

    Args:
        type_ (str | Unset):
        additional_properties (str | Unset):
        body (PostLinksPublicBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostLinksPublicResponse200 | PostLinksPublicResponse400 | PostLinksPublicResponse401 | PostLinksPublicResponse402 | PostLinksPublicResponse403 | PostLinksPublicResponse404 | PostLinksPublicResponse409 | PostLinksPublicResponse500]
    """

    kwargs = _get_kwargs(
        body=body,
        type_=type_,
        additional_properties=additional_properties,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: PostLinksPublicBody,
    type_: str | Unset = UNSET,
    additional_properties: str | Unset = UNSET,
) -> (
    PostLinksPublicResponse200
    | PostLinksPublicResponse400
    | PostLinksPublicResponse401
    | PostLinksPublicResponse402
    | PostLinksPublicResponse403
    | PostLinksPublicResponse404
    | PostLinksPublicResponse409
    | PostLinksPublicResponse500
    | None
):
    r"""Create a new link using public API key

     This method creates a new link. Only this method should be used in client-side applications

    If parameter \"path\" is omitted, it generates path by algorithm, chosen in domain settings.

    You can use it with public API key in your frontend applications (client-side javascript, Android &
    iPhone apps)
    **Rate limit**: 50/s

    Args:
        type_ (str | Unset):
        additional_properties (str | Unset):
        body (PostLinksPublicBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostLinksPublicResponse200 | PostLinksPublicResponse400 | PostLinksPublicResponse401 | PostLinksPublicResponse402 | PostLinksPublicResponse403 | PostLinksPublicResponse404 | PostLinksPublicResponse409 | PostLinksPublicResponse500
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            type_=type_,
            additional_properties=additional_properties,
        )
    ).parsed
