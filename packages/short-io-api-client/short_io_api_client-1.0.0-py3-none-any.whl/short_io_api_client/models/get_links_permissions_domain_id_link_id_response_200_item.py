from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="GetLinksPermissionsDomainIdLinkIdResponse200Item")


@_attrs_define
class GetLinksPermissionsDomainIdLinkIdResponse200Item:
    """
    Attributes:
        id (str):
        domain_id (int):
        user_id (int):
        link_id_string (str):
    """

    id: str
    domain_id: int
    user_id: int
    link_id_string: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        domain_id = self.domain_id

        user_id = self.user_id

        link_id_string = self.link_id_string

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "DomainId": domain_id,
                "UserId": user_id,
                "LinkIdString": link_id_string,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        domain_id = d.pop("DomainId")

        user_id = d.pop("UserId")

        link_id_string = d.pop("LinkIdString")

        get_links_permissions_domain_id_link_id_response_200_item = cls(
            id=id,
            domain_id=domain_id,
            user_id=user_id,
            link_id_string=link_id_string,
        )

        get_links_permissions_domain_id_link_id_response_200_item.additional_properties = d
        return get_links_permissions_domain_id_link_id_response_200_item

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
