from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_links_delete_bulk_body import DeleteLinksDeleteBulkBody
from ...models.delete_links_delete_bulk_response_200 import DeleteLinksDeleteBulkResponse200
from ...types import Response


def _get_kwargs(
    *,
    body: DeleteLinksDeleteBulkBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/links/delete_bulk",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DeleteLinksDeleteBulkResponse200 | None:
    if response.status_code == 200:
        response_200 = DeleteLinksDeleteBulkResponse200.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[DeleteLinksDeleteBulkResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DeleteLinksDeleteBulkBody,
) -> Response[DeleteLinksDeleteBulkResponse200]:
    """Delete links in bulk

     Delete links in bulk by ids

    **Rate limit**: 1/s

    Args:
        body (DeleteLinksDeleteBulkBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteLinksDeleteBulkResponse200]
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
    body: DeleteLinksDeleteBulkBody,
) -> DeleteLinksDeleteBulkResponse200 | None:
    """Delete links in bulk

     Delete links in bulk by ids

    **Rate limit**: 1/s

    Args:
        body (DeleteLinksDeleteBulkBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteLinksDeleteBulkResponse200
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DeleteLinksDeleteBulkBody,
) -> Response[DeleteLinksDeleteBulkResponse200]:
    """Delete links in bulk

     Delete links in bulk by ids

    **Rate limit**: 1/s

    Args:
        body (DeleteLinksDeleteBulkBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteLinksDeleteBulkResponse200]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: DeleteLinksDeleteBulkBody,
) -> DeleteLinksDeleteBulkResponse200 | None:
    """Delete links in bulk

     Delete links in bulk by ids

    **Rate limit**: 1/s

    Args:
        body (DeleteLinksDeleteBulkBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteLinksDeleteBulkResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
