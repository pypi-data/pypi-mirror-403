from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="PostLinksDuplicateLinkIdResponse200")


@_attrs_define
class PostLinksDuplicateLinkIdResponse200:
    """
    Attributes:
        duplicated_from (str): Original link's idString
    """

    duplicated_from: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        duplicated_from = self.duplicated_from

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "duplicatedFrom": duplicated_from,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        duplicated_from = d.pop("duplicatedFrom")

        post_links_duplicate_link_id_response_200 = cls(
            duplicated_from=duplicated_from,
        )

        post_links_duplicate_link_id_response_200.additional_properties = d
        return post_links_duplicate_link_id_response_200

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
