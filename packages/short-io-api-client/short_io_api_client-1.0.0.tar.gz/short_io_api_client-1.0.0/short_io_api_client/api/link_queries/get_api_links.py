import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_api_links_date_sort_order import GetApiLinksDateSortOrder
from ...models.get_api_links_response_200 import GetApiLinksResponse200
from ...models.get_api_links_response_402 import GetApiLinksResponse402
from ...models.get_api_links_response_403 import GetApiLinksResponse403
from ...models.get_api_links_response_404 import GetApiLinksResponse404
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    domain_id: int,
    limit: int | None | Unset = UNSET,
    id_string: str | Unset = UNSET,
    created_at: str | Unset = UNSET,
    before_date: datetime.datetime | Unset = UNSET,
    after_date: datetime.datetime | Unset = UNSET,
    date_sort_order: GetApiLinksDateSortOrder | Unset = UNSET,
    page_token: str | Unset = UNSET,
    folder_id: str | Unset = UNSET,
    x_vercel_id: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_vercel_id, Unset):
        headers["x-vercel-id"] = x_vercel_id

    params: dict[str, Any] = {}

    params["domain_id"] = domain_id

    json_limit: int | None | Unset
    if isinstance(limit, Unset):
        json_limit = UNSET
    else:
        json_limit = limit
    params["limit"] = json_limit

    params["idString"] = id_string

    params["createdAt"] = created_at

    json_before_date: str | Unset = UNSET
    if not isinstance(before_date, Unset):
        json_before_date = before_date.isoformat()
    params["beforeDate"] = json_before_date

    json_after_date: str | Unset = UNSET
    if not isinstance(after_date, Unset):
        json_after_date = after_date.isoformat()
    params["afterDate"] = json_after_date

    json_date_sort_order: str | Unset = UNSET
    if not isinstance(date_sort_order, Unset):
        json_date_sort_order = date_sort_order.value

    params["dateSortOrder"] = json_date_sort_order

    params["pageToken"] = page_token

    params["folderId"] = folder_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/links",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GetApiLinksResponse200 | GetApiLinksResponse402 | GetApiLinksResponse403 | GetApiLinksResponse404 | None:
    if response.status_code == 200:
        response_200 = GetApiLinksResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 402:
        response_402 = GetApiLinksResponse402.from_dict(response.json())

        return response_402

    if response.status_code == 403:
        response_403 = GetApiLinksResponse403.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = GetApiLinksResponse404.from_dict(response.json())

        return response_404

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[GetApiLinksResponse200 | GetApiLinksResponse402 | GetApiLinksResponse403 | GetApiLinksResponse404]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    domain_id: int,
    limit: int | None | Unset = UNSET,
    id_string: str | Unset = UNSET,
    created_at: str | Unset = UNSET,
    before_date: datetime.datetime | Unset = UNSET,
    after_date: datetime.datetime | Unset = UNSET,
    date_sort_order: GetApiLinksDateSortOrder | Unset = UNSET,
    page_token: str | Unset = UNSET,
    folder_id: str | Unset = UNSET,
    x_vercel_id: str | Unset = UNSET,
) -> Response[GetApiLinksResponse200 | GetApiLinksResponse402 | GetApiLinksResponse403 | GetApiLinksResponse404]:
    """Link list

     Get domain links

    Args:
        domain_id (int):
        limit (int | None | Unset):
        id_string (str | Unset):
        created_at (str | Unset):
        before_date (datetime.datetime | Unset):
        after_date (datetime.datetime | Unset):
        date_sort_order (GetApiLinksDateSortOrder | Unset):
        page_token (str | Unset):
        folder_id (str | Unset):
        x_vercel_id (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetApiLinksResponse200 | GetApiLinksResponse402 | GetApiLinksResponse403 | GetApiLinksResponse404]
    """

    kwargs = _get_kwargs(
        domain_id=domain_id,
        limit=limit,
        id_string=id_string,
        created_at=created_at,
        before_date=before_date,
        after_date=after_date,
        date_sort_order=date_sort_order,
        page_token=page_token,
        folder_id=folder_id,
        x_vercel_id=x_vercel_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    domain_id: int,
    limit: int | None | Unset = UNSET,
    id_string: str | Unset = UNSET,
    created_at: str | Unset = UNSET,
    before_date: datetime.datetime | Unset = UNSET,
    after_date: datetime.datetime | Unset = UNSET,
    date_sort_order: GetApiLinksDateSortOrder | Unset = UNSET,
    page_token: str | Unset = UNSET,
    folder_id: str | Unset = UNSET,
    x_vercel_id: str | Unset = UNSET,
) -> GetApiLinksResponse200 | GetApiLinksResponse402 | GetApiLinksResponse403 | GetApiLinksResponse404 | None:
    """Link list

     Get domain links

    Args:
        domain_id (int):
        limit (int | None | Unset):
        id_string (str | Unset):
        created_at (str | Unset):
        before_date (datetime.datetime | Unset):
        after_date (datetime.datetime | Unset):
        date_sort_order (GetApiLinksDateSortOrder | Unset):
        page_token (str | Unset):
        folder_id (str | Unset):
        x_vercel_id (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetApiLinksResponse200 | GetApiLinksResponse402 | GetApiLinksResponse403 | GetApiLinksResponse404
    """

    return sync_detailed(
        client=client,
        domain_id=domain_id,
        limit=limit,
        id_string=id_string,
        created_at=created_at,
        before_date=before_date,
        after_date=after_date,
        date_sort_order=date_sort_order,
        page_token=page_token,
        folder_id=folder_id,
        x_vercel_id=x_vercel_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    domain_id: int,
    limit: int | None | Unset = UNSET,
    id_string: str | Unset = UNSET,
    created_at: str | Unset = UNSET,
    before_date: datetime.datetime | Unset = UNSET,
    after_date: datetime.datetime | Unset = UNSET,
    date_sort_order: GetApiLinksDateSortOrder | Unset = UNSET,
    page_token: str | Unset = UNSET,
    folder_id: str | Unset = UNSET,
    x_vercel_id: str | Unset = UNSET,
) -> Response[GetApiLinksResponse200 | GetApiLinksResponse402 | GetApiLinksResponse403 | GetApiLinksResponse404]:
    """Link list

     Get domain links

    Args:
        domain_id (int):
        limit (int | None | Unset):
        id_string (str | Unset):
        created_at (str | Unset):
        before_date (datetime.datetime | Unset):
        after_date (datetime.datetime | Unset):
        date_sort_order (GetApiLinksDateSortOrder | Unset):
        page_token (str | Unset):
        folder_id (str | Unset):
        x_vercel_id (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetApiLinksResponse200 | GetApiLinksResponse402 | GetApiLinksResponse403 | GetApiLinksResponse404]
    """

    kwargs = _get_kwargs(
        domain_id=domain_id,
        limit=limit,
        id_string=id_string,
        created_at=created_at,
        before_date=before_date,
        after_date=after_date,
        date_sort_order=date_sort_order,
        page_token=page_token,
        folder_id=folder_id,
        x_vercel_id=x_vercel_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    domain_id: int,
    limit: int | None | Unset = UNSET,
    id_string: str | Unset = UNSET,
    created_at: str | Unset = UNSET,
    before_date: datetime.datetime | Unset = UNSET,
    after_date: datetime.datetime | Unset = UNSET,
    date_sort_order: GetApiLinksDateSortOrder | Unset = UNSET,
    page_token: str | Unset = UNSET,
    folder_id: str | Unset = UNSET,
    x_vercel_id: str | Unset = UNSET,
) -> GetApiLinksResponse200 | GetApiLinksResponse402 | GetApiLinksResponse403 | GetApiLinksResponse404 | None:
    """Link list

     Get domain links

    Args:
        domain_id (int):
        limit (int | None | Unset):
        id_string (str | Unset):
        created_at (str | Unset):
        before_date (datetime.datetime | Unset):
        after_date (datetime.datetime | Unset):
        date_sort_order (GetApiLinksDateSortOrder | Unset):
        page_token (str | Unset):
        folder_id (str | Unset):
        x_vercel_id (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetApiLinksResponse200 | GetApiLinksResponse402 | GetApiLinksResponse403 | GetApiLinksResponse404
    """

    return (
        await asyncio_detailed(
            client=client,
            domain_id=domain_id,
            limit=limit,
            id_string=id_string,
            created_at=created_at,
            before_date=before_date,
            after_date=after_date,
            date_sort_order=date_sort_order,
            page_token=page_token,
            folder_id=folder_id,
            x_vercel_id=x_vercel_id,
        )
    ).parsed
