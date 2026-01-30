from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.post_domains_body_link_type import PostDomainsBodyLinkType
from ..types import UNSET, Unset

T = TypeVar("T", bound="PostDomainsBody")


@_attrs_define
class PostDomainsBody:
    """
    Attributes:
        hostname (str): Domain hostname Example: 😀.link.
        hide_referer (bool | Unset):
        link_type (PostDomainsBodyLinkType | Unset):
    """

    hostname: str
    hide_referer: bool | Unset = UNSET
    link_type: PostDomainsBodyLinkType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        hostname = self.hostname

        hide_referer = self.hide_referer

        link_type: str | Unset = UNSET
        if not isinstance(self.link_type, Unset):
            link_type = self.link_type.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "hostname": hostname,
            }
        )
        if hide_referer is not UNSET:
            field_dict["hideReferer"] = hide_referer
        if link_type is not UNSET:
            field_dict["linkType"] = link_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        hostname = d.pop("hostname")

        hide_referer = d.pop("hideReferer", UNSET)

        _link_type = d.pop("linkType", UNSET)
        link_type: PostDomainsBodyLinkType | Unset
        if isinstance(_link_type, Unset):
            link_type = UNSET
        else:
            link_type = PostDomainsBodyLinkType(_link_type)

        post_domains_body = cls(
            hostname=hostname,
            hide_referer=hide_referer,
            link_type=link_type,
        )

        post_domains_body.additional_properties = d
        return post_domains_body

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
