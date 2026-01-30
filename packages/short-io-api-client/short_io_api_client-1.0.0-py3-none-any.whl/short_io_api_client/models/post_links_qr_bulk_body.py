from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.post_links_qr_bulk_body_type import PostLinksQrBulkBodyType
from ..types import UNSET, Unset

T = TypeVar("T", bound="PostLinksQrBulkBody")


@_attrs_define
class PostLinksQrBulkBody:
    """
    Attributes:
        type_ (PostLinksQrBulkBodyType):  Default: PostLinksQrBulkBodyType.PNG.
        use_domain_settings (bool):  Default: True.
        link_ids (list[str]):
        color (str | Unset):
        background_color (str | Unset):
        size (float | Unset):
        no_excavate (bool | Unset):
        domain_id (str | Unset):
    """

    link_ids: list[str]
    type_: PostLinksQrBulkBodyType = PostLinksQrBulkBodyType.PNG
    use_domain_settings: bool = True
    color: str | Unset = UNSET
    background_color: str | Unset = UNSET
    size: float | Unset = UNSET
    no_excavate: bool | Unset = UNSET
    domain_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        use_domain_settings = self.use_domain_settings

        link_ids = self.link_ids

        color = self.color

        background_color = self.background_color

        size = self.size

        no_excavate = self.no_excavate

        domain_id = self.domain_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "useDomainSettings": use_domain_settings,
                "linkIds": link_ids,
            }
        )
        if color is not UNSET:
            field_dict["color"] = color
        if background_color is not UNSET:
            field_dict["backgroundColor"] = background_color
        if size is not UNSET:
            field_dict["size"] = size
        if no_excavate is not UNSET:
            field_dict["noExcavate"] = no_excavate
        if domain_id is not UNSET:
            field_dict["domainId"] = domain_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = PostLinksQrBulkBodyType(d.pop("type"))

        use_domain_settings = d.pop("useDomainSettings")

        link_ids = cast(list[str], d.pop("linkIds"))

        color = d.pop("color", UNSET)

        background_color = d.pop("backgroundColor", UNSET)

        size = d.pop("size", UNSET)

        no_excavate = d.pop("noExcavate", UNSET)

        domain_id = d.pop("domainId", UNSET)

        post_links_qr_bulk_body = cls(
            type_=type_,
            use_domain_settings=use_domain_settings,
            link_ids=link_ids,
            color=color,
            background_color=background_color,
            size=size,
            no_excavate=no_excavate,
            domain_id=domain_id,
        )

        post_links_qr_bulk_body.additional_properties = d
        return post_links_qr_bulk_body

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
