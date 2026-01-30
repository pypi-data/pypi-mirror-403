from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.post_links_examples_response_200_links_item import PostLinksExamplesResponse200LinksItem


T = TypeVar("T", bound="PostLinksExamplesResponse200")


@_attrs_define
class PostLinksExamplesResponse200:
    """
    Attributes:
        success (bool):
        links (list[PostLinksExamplesResponse200LinksItem]):
    """

    success: bool
    links: list[PostLinksExamplesResponse200LinksItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        success = self.success

        links = []
        for links_item_data in self.links:
            links_item = links_item_data.to_dict()
            links.append(links_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "success": success,
                "links": links,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_links_examples_response_200_links_item import PostLinksExamplesResponse200LinksItem

        d = dict(src_dict)
        success = d.pop("success")

        links = []
        _links = d.pop("links")
        for links_item_data in _links:
            links_item = PostLinksExamplesResponse200LinksItem.from_dict(links_item_data)

            links.append(links_item)

        post_links_examples_response_200 = cls(
            success=success,
            links=links,
        )

        post_links_examples_response_200.additional_properties = d
        return post_links_examples_response_200

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
