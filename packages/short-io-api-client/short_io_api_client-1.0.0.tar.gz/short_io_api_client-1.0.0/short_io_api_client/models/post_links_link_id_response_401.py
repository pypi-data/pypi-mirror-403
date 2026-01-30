from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PostLinksLinkIdResponse401")


@_attrs_define
class PostLinksLinkIdResponse401:
    """
    Attributes:
        message (str):
        field (str | Unset):
        link_id (str | Unset):
    """

    message: str
    field: str | Unset = UNSET
    link_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        field = self.field

        link_id = self.link_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
            }
        )
        if field is not UNSET:
            field_dict["field"] = field
        if link_id is not UNSET:
            field_dict["linkId"] = link_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        message = d.pop("message")

        field = d.pop("field", UNSET)

        link_id = d.pop("linkId", UNSET)

        post_links_link_id_response_401 = cls(
            message=message,
            field=field,
            link_id=link_id,
        )

        post_links_link_id_response_401.additional_properties = d
        return post_links_link_id_response_401

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
