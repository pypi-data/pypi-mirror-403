from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeleteLinksLinkIdResponse200")


@_attrs_define
class DeleteLinksLinkIdResponse200:
    """
    Attributes:
        success (bool):
        id_string (str | Unset): Link ID Example: lnk_abc123_abcdef.
        error (str | Unset):
    """

    success: bool
    id_string: str | Unset = UNSET
    error: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        success = self.success

        id_string = self.id_string

        error = self.error

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "success": success,
            }
        )
        if id_string is not UNSET:
            field_dict["idString"] = id_string
        if error is not UNSET:
            field_dict["error"] = error

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        success = d.pop("success")

        id_string = d.pop("idString", UNSET)

        error = d.pop("error", UNSET)

        delete_links_link_id_response_200 = cls(
            success=success,
            id_string=id_string,
            error=error,
        )

        delete_links_link_id_response_200.additional_properties = d
        return delete_links_link_id_response_200

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
