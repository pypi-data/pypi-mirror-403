from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_links_tweetbot_url_only_type_0 import GetLinksTweetbotUrlOnlyType0
from ...models.get_links_tweetbot_url_only_type_1 import GetLinksTweetbotUrlOnlyType1
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    domain: str,
    path: str | Unset = UNSET,
    original_url: str,
    title: str | Unset = UNSET,
    url_only: bool | GetLinksTweetbotUrlOnlyType0 | GetLinksTweetbotUrlOnlyType1 | Unset = UNSET,
    api_key: str,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["domain"] = domain

    params["path"] = path

    params["originalURL"] = original_url

    params["title"] = title

    json_url_only: bool | str | Unset
    if isinstance(url_only, Unset):
        json_url_only = UNSET
    elif isinstance(url_only, GetLinksTweetbotUrlOnlyType0):
        json_url_only = url_only.value
    elif isinstance(url_only, GetLinksTweetbotUrlOnlyType1):
        json_url_only = url_only.value
    else:
        json_url_only = url_only
    params["urlOnly"] = json_url_only

    params["apiKey"] = api_key

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/links/tweetbot",
        "params": params,
    }

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
    domain: str,
    path: str | Unset = UNSET,
    original_url: str,
    title: str | Unset = UNSET,
    url_only: bool | GetLinksTweetbotUrlOnlyType0 | GetLinksTweetbotUrlOnlyType1 | Unset = UNSET,
    api_key: str,
) -> Response[Any]:
    """Create a new link (simple version)


                        Simple version of link create endpoint. You can use it if you can not use POST
    method
                        **Rate limit**: 50/s


    Args:
        domain (str):
        path (str | Unset):
        original_url (str):
        title (str | Unset):
        url_only (bool | GetLinksTweetbotUrlOnlyType0 | GetLinksTweetbotUrlOnlyType1 | Unset):
        api_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        domain=domain,
        path=path,
        original_url=original_url,
        title=title,
        url_only=url_only,
        api_key=api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    domain: str,
    path: str | Unset = UNSET,
    original_url: str,
    title: str | Unset = UNSET,
    url_only: bool | GetLinksTweetbotUrlOnlyType0 | GetLinksTweetbotUrlOnlyType1 | Unset = UNSET,
    api_key: str,
) -> Response[Any]:
    """Create a new link (simple version)


                        Simple version of link create endpoint. You can use it if you can not use POST
    method
                        **Rate limit**: 50/s


    Args:
        domain (str):
        path (str | Unset):
        original_url (str):
        title (str | Unset):
        url_only (bool | GetLinksTweetbotUrlOnlyType0 | GetLinksTweetbotUrlOnlyType1 | Unset):
        api_key (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        domain=domain,
        path=path,
        original_url=original_url,
        title=title,
        url_only=url_only,
        api_key=api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)
