from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_api_links_response_200_links_item import GetApiLinksResponse200LinksItem


T = TypeVar("T", bound="GetApiLinksResponse200")


@_attrs_define
class GetApiLinksResponse200:
    """
    Attributes:
        count (int):
        links (list[GetApiLinksResponse200LinksItem]):
        next_page_token (None | str | Unset):
    """

    count: int
    links: list[GetApiLinksResponse200LinksItem]
    next_page_token: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        count = self.count

        links = []
        for links_item_data in self.links:
            links_item = links_item_data.to_dict()
            links.append(links_item)

        next_page_token: None | str | Unset
        if isinstance(self.next_page_token, Unset):
            next_page_token = UNSET
        else:
            next_page_token = self.next_page_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "count": count,
                "links": links,
            }
        )
        if next_page_token is not UNSET:
            field_dict["nextPageToken"] = next_page_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_api_links_response_200_links_item import GetApiLinksResponse200LinksItem

        d = dict(src_dict)
        count = d.pop("count")

        links = []
        _links = d.pop("links")
        for links_item_data in _links:
            links_item = GetApiLinksResponse200LinksItem.from_dict(links_item_data)

            links.append(links_item)

        def _parse_next_page_token(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        next_page_token = _parse_next_page_token(d.pop("nextPageToken", UNSET))

        get_api_links_response_200 = cls(
            count=count,
            links=links,
            next_page_token=next_page_token,
        )

        get_api_links_response_200.additional_properties = d
        return get_api_links_response_200

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
