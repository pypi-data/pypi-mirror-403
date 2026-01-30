from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.post_links_bulk_body_links_item import PostLinksBulkBodyLinksItem


T = TypeVar("T", bound="PostLinksBulkBody")


@_attrs_define
class PostLinksBulkBody:
    """
    Attributes:
        domain (str):
        links (list[PostLinksBulkBodyLinksItem]):
        allow_duplicates (bool | Unset):  Default: False.
        folder_id (str | Unset): Folder ID
    """

    domain: str
    links: list[PostLinksBulkBodyLinksItem]
    allow_duplicates: bool | Unset = False
    folder_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        domain = self.domain

        links = []
        for links_item_data in self.links:
            links_item = links_item_data.to_dict()
            links.append(links_item)

        allow_duplicates = self.allow_duplicates

        folder_id = self.folder_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "domain": domain,
                "links": links,
            }
        )
        if allow_duplicates is not UNSET:
            field_dict["allowDuplicates"] = allow_duplicates
        if folder_id is not UNSET:
            field_dict["folderId"] = folder_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_links_bulk_body_links_item import PostLinksBulkBodyLinksItem

        d = dict(src_dict)
        domain = d.pop("domain")

        links = []
        _links = d.pop("links")
        for links_item_data in _links:
            links_item = PostLinksBulkBodyLinksItem.from_dict(links_item_data)

            links.append(links_item)

        allow_duplicates = d.pop("allowDuplicates", UNSET)

        folder_id = d.pop("folderId", UNSET)

        post_links_bulk_body = cls(
            domain=domain,
            links=links,
            allow_duplicates=allow_duplicates,
            folder_id=folder_id,
        )

        post_links_bulk_body.additional_properties = d
        return post_links_bulk_body

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
