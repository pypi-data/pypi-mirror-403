from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.post_link_region_link_id_body_country import PostLinkRegionLinkIdBodyCountry

T = TypeVar("T", bound="PostLinkRegionLinkIdBody")


@_attrs_define
class PostLinkRegionLinkIdBody:
    """
    Attributes:
        country (PostLinkRegionLinkIdBodyCountry): Country code
        region (str): ISO 3166-2 region code
        original_url (str):  Example: https://example.com.
    """

    country: PostLinkRegionLinkIdBodyCountry
    region: str
    original_url: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        country = self.country.value

        region = self.region

        original_url = self.original_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "country": country,
                "region": region,
                "originalURL": original_url,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        country = PostLinkRegionLinkIdBodyCountry(d.pop("country"))

        region = d.pop("region")

        original_url = d.pop("originalURL")

        post_link_region_link_id_body = cls(
            country=country,
            region=region,
            original_url=original_url,
        )

        post_link_region_link_id_body.additional_properties = d
        return post_link_region_link_id_body

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
