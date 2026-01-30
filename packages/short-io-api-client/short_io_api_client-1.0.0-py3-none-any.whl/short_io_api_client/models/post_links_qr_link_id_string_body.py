from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.post_links_qr_link_id_string_body_type import PostLinksQrLinkIdStringBodyType
from ..types import UNSET, Unset

T = TypeVar("T", bound="PostLinksQrLinkIdStringBody")


@_attrs_define
class PostLinksQrLinkIdStringBody:
    """
    Attributes:
        use_domain_settings (bool):  Default: True.
        color (str | Unset):
        background_color (str | Unset):
        size (float | Unset):
        type_ (PostLinksQrLinkIdStringBodyType | Unset):  Default: PostLinksQrLinkIdStringBodyType.PNG.
    """

    use_domain_settings: bool = True
    color: str | Unset = UNSET
    background_color: str | Unset = UNSET
    size: float | Unset = UNSET
    type_: PostLinksQrLinkIdStringBodyType | Unset = PostLinksQrLinkIdStringBodyType.PNG
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        use_domain_settings = self.use_domain_settings

        color = self.color

        background_color = self.background_color

        size = self.size

        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "useDomainSettings": use_domain_settings,
            }
        )
        if color is not UNSET:
            field_dict["color"] = color
        if background_color is not UNSET:
            field_dict["backgroundColor"] = background_color
        if size is not UNSET:
            field_dict["size"] = size
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        use_domain_settings = d.pop("useDomainSettings")

        color = d.pop("color", UNSET)

        background_color = d.pop("backgroundColor", UNSET)

        size = d.pop("size", UNSET)

        _type_ = d.pop("type", UNSET)
        type_: PostLinksQrLinkIdStringBodyType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = PostLinksQrLinkIdStringBodyType(_type_)

        post_links_qr_link_id_string_body = cls(
            use_domain_settings=use_domain_settings,
            color=color,
            background_color=background_color,
            size=size,
            type_=type_,
        )

        post_links_qr_link_id_string_body.additional_properties = d
        return post_links_qr_link_id_string_body

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
