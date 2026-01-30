# short-io-api-client

A Python client library for the [Short.io](https://short.io) API, auto-generated from the [OpenAPI specification](https://api.short.io/openapi.json) using [openapi-python-client](https://github.com/openapi-generators/openapi-python-client).

## Requirements

- Python 3.10+
- [httpx](https://www.python-httpx.org/) >= 0.23.0

## Installation

### Using Poetry

```bash
poetry add /path/to/short-io-api-client
```

### Using pip (from wheel)

```bash
cd short-io-api-client
poetry build -f wheel
pip install dist/short_io_api_client-1.0.0-py3-none-any.whl
```

## Quick Start

### Authentication

All Short.io API endpoints require an API key. Create an `AuthenticatedClient` with your key passed via the `Authorization` header:

```python
from short_io_api_client import AuthenticatedClient

client = AuthenticatedClient(
    base_url="https://api.short.io",
    token="YOUR_API_KEY",
    prefix="",  # Short.io uses a raw API key, not "Bearer <token>"
)
```

### Create a Short Link

```python
from short_io_api_client import AuthenticatedClient
from short_io_api_client.api.link_management import post_links
from short_io_api_client.models import PostLinksBody

client = AuthenticatedClient(
    base_url="https://api.short.io",
    token="YOUR_API_KEY",
    prefix="",
)

with client as c:
    result = post_links.sync(
        client=c,
        body=PostLinksBody(
            original_url="https://example.com/my-long-url",
            domain="your-domain.short.gy",
            path="my-custom-slug",
            title="My Link",
            tags=["marketing", "campaign"],
        ),
    )
    print(result)
```

### List Domains

```python
from short_io_api_client.api.domains import get_api_domains

with client as c:
    domains = get_api_domains.sync(client=c)
    if domains:
        for domain in domains:
            print(domain)
```

### List Links for a Domain

```python
from short_io_api_client.api.link_queries import get_api_links

with client as c:
    result = get_api_links.sync(client=c, domain_id=123456)
    print(result)
```

### Update a Link

```python
from short_io_api_client.api.link_management import post_links_link_id
from short_io_api_client.models import PostLinksLinkIdBody

with client as c:
    result = post_links_link_id.sync(
        link_id="lnk_abc123",
        client=c,
        body=PostLinksLinkIdBody(
            original_url="https://example.com/updated-url",
            title="Updated Title",
        ),
    )
    print(result)
```

### Delete a Link

```python
from short_io_api_client.api.link_management import delete_links_link_id

with client as c:
    result = delete_links_link_id.sync(link_id="lnk_abc123", client=c)
    print(result)
```

### Get Link by Original URL

```python
from short_io_api_client.api.link_queries import get_links_by_original_url

with client as c:
    result = get_links_by_original_url.sync(
        client=c,
        domain="your-domain.short.gy",
        original_url="https://example.com/my-long-url",
    )
    print(result)
```

## Async Usage

Every endpoint has async variants. Replace `.sync()` with `.asyncio()`:

```python
import asyncio
from short_io_api_client import AuthenticatedClient
from short_io_api_client.api.link_management import post_links
from short_io_api_client.models import PostLinksBody

client = AuthenticatedClient(
    base_url="https://api.short.io",
    token="YOUR_API_KEY",
    prefix="",
)

async def main():
    async with client as c:
        result = await post_links.asyncio(
            client=c,
            body=PostLinksBody(
                original_url="https://example.com",
                domain="your-domain.short.gy",
            ),
        )
        print(result)

asyncio.run(main())
```

## Detailed Responses

Use the `_detailed` variants to get full HTTP response information:

```python
from short_io_api_client.api.link_management import post_links
from short_io_api_client.types import Response

with client as c:
    response: Response = post_links.sync_detailed(
        client=c,
        body=PostLinksBody(
            original_url="https://example.com",
            domain="your-domain.short.gy",
        ),
    )
    print(response.status_code)  # HTTPStatus enum
    print(response.headers)      # dict
    print(response.parsed)       # parsed model or None
    print(response.content)      # raw bytes
```

## Error Handling

Enable `raise_on_unexpected_status` to raise on undocumented status codes:

```python
client = AuthenticatedClient(
    base_url="https://api.short.io",
    token="YOUR_API_KEY",
    prefix="",
    raise_on_unexpected_status=True,
)
```

Documented error responses (400, 401, 402, 403, 404, 409, 500) are returned as typed model objects. Check the response type to handle errors:

```python
from short_io_api_client.models import PostLinksResponse200, PostLinksResponse409

result = post_links.sync(client=c, body=body)

if isinstance(result, PostLinksResponse200):
    print("Created:", result)
elif isinstance(result, PostLinksResponse409):
    print("Conflict: link path already exists")
```

## API Modules

| Module | Description |
|--------|-------------|
| `api.link_management` | Create, update, delete, archive, bulk operations, QR codes, permissions |
| `api.link_queries` | List links, get by ID/URL, folders, OpenGraph data |
| `api.link_targeting` | Country and region-based link targeting |
| `api.domains` | List, get, create, and configure domains |

### Link Management Endpoints

| Function | Description |
|----------|-------------|
| `post_links` | Create a new short link |
| `post_links_link_id` | Update a link by ID |
| `delete_links_link_id` | Delete a link by ID |
| `delete_links_delete_bulk` | Bulk delete links |
| `post_links_bulk` | Bulk create links |
| `post_links_archive` | Archive a link |
| `post_links_unarchive` | Unarchive a link |
| `post_links_archive_bulk` | Bulk archive links |
| `post_links_unarchive_bulk` | Bulk unarchive links |
| `post_links_duplicate_link_id` | Duplicate a link |
| `post_links_qr_link_id_string` | Generate QR code for a link |
| `post_links_qr_bulk` | Bulk generate QR codes |
| `post_links_public` | Create a public link |
| `post_links_examples` | Get link examples |
| `post_tags_bulk` | Bulk tag operations |
| `put_links_opengraph_domain_id_link_id` | Update OpenGraph data |
| `get_links_permissions_domain_id_link_id` | Get link permissions |
| `post_links_permissions_domain_id_link_id_user_id` | Set link permissions |
| `delete_links_permissions_domain_id_link_id_user_id` | Remove link permissions |
| `get_links_tweetbot` | Tweetbot integration |

### Link Query Endpoints

| Function | Description |
|----------|-------------|
| `get_api_links` | List links for a domain |
| `get_links_link_id` | Get link by ID |
| `get_links_by_original_url` | Get link by original URL |
| `get_links_expand` | Expand a short link |
| `get_links_multiple_by_url` | Get multiple links by URL |
| `get_links_opengraph_domain_id_link_id` | Get OpenGraph data |
| `get_links_folders_domain_id` | List folders for a domain |
| `get_links_folders_domain_id_folder_id` | Get folder by ID |
| `post_links_folders` | Create a folder |

### Domain Endpoints

| Function | Description |
|----------|-------------|
| `get_api_domains` | List all domains |
| `get_domains_domain_id` | Get domain by ID |
| `post_domains` | Create a new domain |
| `post_domains_settings_domain_id` | Update domain settings |

### Link Targeting Endpoints

| Function | Description |
|----------|-------------|
| `get_link_country_link_id` | Get country targeting rules |
| `post_link_country_link_id` | Set country targeting |
| `post_link_country_bulk_link_id` | Bulk set country targeting |
| `delete_link_country_link_id_country` | Delete country targeting rule |
| `get_link_region_link_id` | Get region targeting rules |
| `post_link_region_link_id` | Set region targeting |
| `post_link_region_bulk_link_id` | Bulk set region targeting |
| `delete_link_region_link_id_country_region` | Delete region targeting rule |
| `get_link_region_list_country` | List regions for a country |

## Advanced Configuration

### Custom Timeout

```python
import httpx

client = AuthenticatedClient(
    base_url="https://api.short.io",
    token="YOUR_API_KEY",
    prefix="",
    timeout=httpx.Timeout(30.0),
)
```

### Request/Response Logging

```python
client = AuthenticatedClient(
    base_url="https://api.short.io",
    token="YOUR_API_KEY",
    prefix="",
    httpx_args={
        "event_hooks": {
            "request": [lambda r: print(f"-> {r.method} {r.url}")],
            "response": [lambda r: print(f"<- {r.status_code}")],
        }
    },
)
```

### Custom SSL Certificate

```python
client = AuthenticatedClient(
    base_url="https://api.short.io",
    token="YOUR_API_KEY",
    prefix="",
    verify_ssl="/path/to/certificate_bundle.pem",
)
```

## Function Variants

Every endpoint module provides four functions:

| Function | Description |
|----------|-------------|
| `sync` | Blocking call, returns parsed response model or `None` |
| `sync_detailed` | Blocking call, returns `Response` with status, headers, and parsed body |
| `asyncio` | Async call, returns parsed response model or `None` |
| `asyncio_detailed` | Async call, returns `Response` with status, headers, and parsed body |

## Building / Publishing

This project uses [Poetry](https://python-poetry.org/) for dependency management and packaging:

```bash
# Build a wheel
poetry build -f wheel

# Publish to PyPI
poetry publish --build

# Publish to a private repository
poetry config repositories.my-repo https://my-repo.example.com/simple/
poetry publish --build -r my-repo
```
