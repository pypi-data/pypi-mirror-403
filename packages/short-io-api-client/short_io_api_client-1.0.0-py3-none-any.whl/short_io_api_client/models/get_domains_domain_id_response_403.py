from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.get_domains_domain_id_response_403_type import GetDomainsDomainIdResponse403Type
from ..types import UNSET, Unset

T = TypeVar("T", bound="GetDomainsDomainIdResponse403")


@_attrs_define
class GetDomainsDomainIdResponse403:
    """
    Attributes:
        error (str):
        type_ (GetDomainsDomainIdResponse403Type | Unset):
    """

    error: str
    type_: GetDomainsDomainIdResponse403Type | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        error = self.error

        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "error": error,
            }
        )
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        error = d.pop("error")

        _type_ = d.pop("type", UNSET)
        type_: GetDomainsDomainIdResponse403Type | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = GetDomainsDomainIdResponse403Type(_type_)

        get_domains_domain_id_response_403 = cls(
            error=error,
            type_=type_,
        )

        get_domains_domain_id_response_403.additional_properties = d
        return get_domains_domain_id_response_403

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
