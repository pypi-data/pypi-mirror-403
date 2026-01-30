from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="PostLinksPublicResponse401")


@_attrs_define
class PostLinksPublicResponse401:
    """
    Attributes:
        message (str):
        success (bool):  Default: False.
        status_code (int):  Default: 401.
    """

    message: str
    success: bool = False
    status_code: int = 401
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        success = self.success

        status_code = self.status_code

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "success": success,
                "statusCode": status_code,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        message = d.pop("message")

        success = d.pop("success")

        status_code = d.pop("statusCode")

        post_links_public_response_401 = cls(
            message=message,
            success=success,
            status_code=status_code,
        )

        post_links_public_response_401.additional_properties = d
        return post_links_public_response_401

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
