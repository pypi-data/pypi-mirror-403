from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PostLinksArchiveBulkBody")


@_attrs_define
class PostLinksArchiveBulkBody:
    """
    Attributes:
        link_ids (list[str]):
        domain_id (str | Unset):
    """

    link_ids: list[str]
    domain_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        link_ids = self.link_ids

        domain_id = self.domain_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "link_ids": link_ids,
            }
        )
        if domain_id is not UNSET:
            field_dict["domain_id"] = domain_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        link_ids = cast(list[str], d.pop("link_ids"))

        domain_id = d.pop("domain_id", UNSET)

        post_links_archive_bulk_body = cls(
            link_ids=link_ids,
            domain_id=domain_id,
        )

        post_links_archive_bulk_body.additional_properties = d
        return post_links_archive_bulk_body

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
