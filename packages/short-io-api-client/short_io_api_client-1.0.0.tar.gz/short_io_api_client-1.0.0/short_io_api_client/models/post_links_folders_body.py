from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PostLinksFoldersBody")


@_attrs_define
class PostLinksFoldersBody:
    """
    Attributes:
        domain_id (int):
        name (str):
        color (str | Unset):
        background_color (str | Unset):
        logo_url (str | Unset):
        logo_height (int | Unset):
        logo_width (int | Unset):
        ec_level (str | Unset):
        integration_fb (str | Unset):
        integration_tt (str | Unset):
        integration_ga (str | Unset):
        integration_gtm (str | Unset):
        integration_adroll (str | Unset):
        utm_campaign (str | Unset):
        utm_medium (str | Unset):
        utm_source (str | Unset):
        utm_term (str | Unset):
        utm_content (str | Unset):
        redirect_type (int | Unset):
        expires_at_days (int | Unset):
        icon (str | Unset):
        prefix (str | Unset):
    """

    domain_id: int
    name: str
    color: str | Unset = UNSET
    background_color: str | Unset = UNSET
    logo_url: str | Unset = UNSET
    logo_height: int | Unset = UNSET
    logo_width: int | Unset = UNSET
    ec_level: str | Unset = UNSET
    integration_fb: str | Unset = UNSET
    integration_tt: str | Unset = UNSET
    integration_ga: str | Unset = UNSET
    integration_gtm: str | Unset = UNSET
    integration_adroll: str | Unset = UNSET
    utm_campaign: str | Unset = UNSET
    utm_medium: str | Unset = UNSET
    utm_source: str | Unset = UNSET
    utm_term: str | Unset = UNSET
    utm_content: str | Unset = UNSET
    redirect_type: int | Unset = UNSET
    expires_at_days: int | Unset = UNSET
    icon: str | Unset = UNSET
    prefix: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        domain_id = self.domain_id

        name = self.name

        color = self.color

        background_color = self.background_color

        logo_url = self.logo_url

        logo_height = self.logo_height

        logo_width = self.logo_width

        ec_level = self.ec_level

        integration_fb = self.integration_fb

        integration_tt = self.integration_tt

        integration_ga = self.integration_ga

        integration_gtm = self.integration_gtm

        integration_adroll = self.integration_adroll

        utm_campaign = self.utm_campaign

        utm_medium = self.utm_medium

        utm_source = self.utm_source

        utm_term = self.utm_term

        utm_content = self.utm_content

        redirect_type = self.redirect_type

        expires_at_days = self.expires_at_days

        icon = self.icon

        prefix = self.prefix

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "domainId": domain_id,
                "name": name,
            }
        )
        if color is not UNSET:
            field_dict["color"] = color
        if background_color is not UNSET:
            field_dict["backgroundColor"] = background_color
        if logo_url is not UNSET:
            field_dict["logoUrl"] = logo_url
        if logo_height is not UNSET:
            field_dict["logoHeight"] = logo_height
        if logo_width is not UNSET:
            field_dict["logoWidth"] = logo_width
        if ec_level is not UNSET:
            field_dict["ecLevel"] = ec_level
        if integration_fb is not UNSET:
            field_dict["integrationFB"] = integration_fb
        if integration_tt is not UNSET:
            field_dict["integrationTT"] = integration_tt
        if integration_ga is not UNSET:
            field_dict["integrationGA"] = integration_ga
        if integration_gtm is not UNSET:
            field_dict["integrationGTM"] = integration_gtm
        if integration_adroll is not UNSET:
            field_dict["integrationAdroll"] = integration_adroll
        if utm_campaign is not UNSET:
            field_dict["utmCampaign"] = utm_campaign
        if utm_medium is not UNSET:
            field_dict["utmMedium"] = utm_medium
        if utm_source is not UNSET:
            field_dict["utmSource"] = utm_source
        if utm_term is not UNSET:
            field_dict["utmTerm"] = utm_term
        if utm_content is not UNSET:
            field_dict["utmContent"] = utm_content
        if redirect_type is not UNSET:
            field_dict["redirectType"] = redirect_type
        if expires_at_days is not UNSET:
            field_dict["expiresAtDays"] = expires_at_days
        if icon is not UNSET:
            field_dict["icon"] = icon
        if prefix is not UNSET:
            field_dict["prefix"] = prefix

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        domain_id = d.pop("domainId")

        name = d.pop("name")

        color = d.pop("color", UNSET)

        background_color = d.pop("backgroundColor", UNSET)

        logo_url = d.pop("logoUrl", UNSET)

        logo_height = d.pop("logoHeight", UNSET)

        logo_width = d.pop("logoWidth", UNSET)

        ec_level = d.pop("ecLevel", UNSET)

        integration_fb = d.pop("integrationFB", UNSET)

        integration_tt = d.pop("integrationTT", UNSET)

        integration_ga = d.pop("integrationGA", UNSET)

        integration_gtm = d.pop("integrationGTM", UNSET)

        integration_adroll = d.pop("integrationAdroll", UNSET)

        utm_campaign = d.pop("utmCampaign", UNSET)

        utm_medium = d.pop("utmMedium", UNSET)

        utm_source = d.pop("utmSource", UNSET)

        utm_term = d.pop("utmTerm", UNSET)

        utm_content = d.pop("utmContent", UNSET)

        redirect_type = d.pop("redirectType", UNSET)

        expires_at_days = d.pop("expiresAtDays", UNSET)

        icon = d.pop("icon", UNSET)

        prefix = d.pop("prefix", UNSET)

        post_links_folders_body = cls(
            domain_id=domain_id,
            name=name,
            color=color,
            background_color=background_color,
            logo_url=logo_url,
            logo_height=logo_height,
            logo_width=logo_width,
            ec_level=ec_level,
            integration_fb=integration_fb,
            integration_tt=integration_tt,
            integration_ga=integration_ga,
            integration_gtm=integration_gtm,
            integration_adroll=integration_adroll,
            utm_campaign=utm_campaign,
            utm_medium=utm_medium,
            utm_source=utm_source,
            utm_term=utm_term,
            utm_content=utm_content,
            redirect_type=redirect_type,
            expires_at_days=expires_at_days,
            icon=icon,
            prefix=prefix,
        )

        post_links_folders_body.additional_properties = d
        return post_links_folders_body

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
