from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PostLinksResponse400")


@_attrs_define
class PostLinksResponse400:
    """
    Attributes:
        message (str):
        status_code (int):  Default: 400.
        code (str | Unset):
        success (bool | Unset):  Default: False.
    """

    message: str
    status_code: int = 400
    code: str | Unset = UNSET
    success: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        status_code = self.status_code

        code = self.code

        success = self.success

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "statusCode": status_code,
            }
        )
        if code is not UNSET:
            field_dict["code"] = code
        if success is not UNSET:
            field_dict["success"] = success

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        message = d.pop("message")

        status_code = d.pop("statusCode")

        code = d.pop("code", UNSET)

        success = d.pop("success", UNSET)

        post_links_response_400 = cls(
            message=message,
            status_code=status_code,
            code=code,
            success=success,
        )

        post_links_response_400.additional_properties = d
        return post_links_response_400

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
