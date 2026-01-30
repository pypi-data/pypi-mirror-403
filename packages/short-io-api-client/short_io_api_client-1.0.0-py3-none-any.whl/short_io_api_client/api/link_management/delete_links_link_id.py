from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_links_link_id_response_200 import DeleteLinksLinkIdResponse200
from ...models.delete_links_link_id_response_400 import DeleteLinksLinkIdResponse400
from ...models.delete_links_link_id_response_401 import DeleteLinksLinkIdResponse401
from ...models.delete_links_link_id_response_402 import DeleteLinksLinkIdResponse402
from ...models.delete_links_link_id_response_403 import DeleteLinksLinkIdResponse403
from ...models.delete_links_link_id_response_404 import DeleteLinksLinkIdResponse404
from ...models.delete_links_link_id_response_409 import DeleteLinksLinkIdResponse409
from ...models.delete_links_link_id_response_500 import DeleteLinksLinkIdResponse500
from ...types import Response


def _get_kwargs(
    link_id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/links/{link_id}".format(
            link_id=quote(str(link_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    DeleteLinksLinkIdResponse200
    | DeleteLinksLinkIdResponse400
    | DeleteLinksLinkIdResponse401
    | DeleteLinksLinkIdResponse402
    | DeleteLinksLinkIdResponse403
    | DeleteLinksLinkIdResponse404
    | DeleteLinksLinkIdResponse409
    | DeleteLinksLinkIdResponse500
    | None
):
    if response.status_code == 200:
        response_200 = DeleteLinksLinkIdResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = DeleteLinksLinkIdResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = DeleteLinksLinkIdResponse401.from_dict(response.json())

        return response_401

    if response.status_code == 402:
        response_402 = DeleteLinksLinkIdResponse402.from_dict(response.json())

        return response_402

    if response.status_code == 403:
        response_403 = DeleteLinksLinkIdResponse403.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = DeleteLinksLinkIdResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = DeleteLinksLinkIdResponse409.from_dict(response.json())

        return response_409

    if response.status_code == 500:
        response_500 = DeleteLinksLinkIdResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    DeleteLinksLinkIdResponse200
    | DeleteLinksLinkIdResponse400
    | DeleteLinksLinkIdResponse401
    | DeleteLinksLinkIdResponse402
    | DeleteLinksLinkIdResponse403
    | DeleteLinksLinkIdResponse404
    | DeleteLinksLinkIdResponse409
    | DeleteLinksLinkIdResponse500
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
) -> Response[
    DeleteLinksLinkIdResponse200
    | DeleteLinksLinkIdResponse400
    | DeleteLinksLinkIdResponse401
    | DeleteLinksLinkIdResponse402
    | DeleteLinksLinkIdResponse403
    | DeleteLinksLinkIdResponse404
    | DeleteLinksLinkIdResponse409
    | DeleteLinksLinkIdResponse500
]:
    """Delete link

     Delete link by id

    **Rate limit**: 20/s

    Args:
        link_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteLinksLinkIdResponse200 | DeleteLinksLinkIdResponse400 | DeleteLinksLinkIdResponse401 | DeleteLinksLinkIdResponse402 | DeleteLinksLinkIdResponse403 | DeleteLinksLinkIdResponse404 | DeleteLinksLinkIdResponse409 | DeleteLinksLinkIdResponse500]
    """

    kwargs = _get_kwargs(
        link_id=link_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    DeleteLinksLinkIdResponse200
    | DeleteLinksLinkIdResponse400
    | DeleteLinksLinkIdResponse401
    | DeleteLinksLinkIdResponse402
    | DeleteLinksLinkIdResponse403
    | DeleteLinksLinkIdResponse404
    | DeleteLinksLinkIdResponse409
    | DeleteLinksLinkIdResponse500
    | None
):
    """Delete link

     Delete link by id

    **Rate limit**: 20/s

    Args:
        link_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteLinksLinkIdResponse200 | DeleteLinksLinkIdResponse400 | DeleteLinksLinkIdResponse401 | DeleteLinksLinkIdResponse402 | DeleteLinksLinkIdResponse403 | DeleteLinksLinkIdResponse404 | DeleteLinksLinkIdResponse409 | DeleteLinksLinkIdResponse500
    """

    return sync_detailed(
        link_id=link_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    DeleteLinksLinkIdResponse200
    | DeleteLinksLinkIdResponse400
    | DeleteLinksLinkIdResponse401
    | DeleteLinksLinkIdResponse402
    | DeleteLinksLinkIdResponse403
    | DeleteLinksLinkIdResponse404
    | DeleteLinksLinkIdResponse409
    | DeleteLinksLinkIdResponse500
]:
    """Delete link

     Delete link by id

    **Rate limit**: 20/s

    Args:
        link_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteLinksLinkIdResponse200 | DeleteLinksLinkIdResponse400 | DeleteLinksLinkIdResponse401 | DeleteLinksLinkIdResponse402 | DeleteLinksLinkIdResponse403 | DeleteLinksLinkIdResponse404 | DeleteLinksLinkIdResponse409 | DeleteLinksLinkIdResponse500]
    """

    kwargs = _get_kwargs(
        link_id=link_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    link_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    DeleteLinksLinkIdResponse200
    | DeleteLinksLinkIdResponse400
    | DeleteLinksLinkIdResponse401
    | DeleteLinksLinkIdResponse402
    | DeleteLinksLinkIdResponse403
    | DeleteLinksLinkIdResponse404
    | DeleteLinksLinkIdResponse409
    | DeleteLinksLinkIdResponse500
    | None
):
    """Delete link

     Delete link by id

    **Rate limit**: 20/s

    Args:
        link_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteLinksLinkIdResponse200 | DeleteLinksLinkIdResponse400 | DeleteLinksLinkIdResponse401 | DeleteLinksLinkIdResponse402 | DeleteLinksLinkIdResponse403 | DeleteLinksLinkIdResponse404 | DeleteLinksLinkIdResponse409 | DeleteLinksLinkIdResponse500
    """

    return (
        await asyncio_detailed(
            link_id=link_id,
            client=client,
        )
    ).parsed
