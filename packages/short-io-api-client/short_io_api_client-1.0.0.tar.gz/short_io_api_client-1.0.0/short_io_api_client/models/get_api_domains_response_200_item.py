from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.get_api_domains_response_200_item_https_level import GetApiDomainsResponse200ItemHttpsLevel
from ..models.get_api_domains_response_200_item_link_type import GetApiDomainsResponse200ItemLinkType
from ..models.get_api_domains_response_200_item_robots import GetApiDomainsResponse200ItemRobots
from ..models.get_api_domains_response_200_item_state import GetApiDomainsResponse200ItemState
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_api_domains_response_200_item_client_storage import GetApiDomainsResponse200ItemClientStorage


T = TypeVar("T", bound="GetApiDomainsResponse200Item")


@_attrs_define
class GetApiDomainsResponse200Item:
    """
    Attributes:
        id (int): Domain ID Example: 12345.
        hostname (str):
        unicode_hostname (str):
        state (GetApiDomainsResponse200ItemState):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        has_favicon (bool):
        hide_referer (bool):
        link_type (GetApiDomainsResponse200ItemLinkType):
        cloaking (bool): Enable cloaking for all links on the domain
        hide_visitor_ip (bool): Don't store visitor IPs in our database
        enable_ai (bool): Enable AI for all links on the domain
        https_level (GetApiDomainsResponse200ItemHttpsLevel):
        https_links (bool | None):
        client_storage (GetApiDomainsResponse200ItemClientStorage):
        case_sensitive (bool):
        increment_counter (str):
        robots (GetApiDomainsResponse200ItemRobots):
        export_enabled (bool):
        enable_conversion_tracking (bool):
        qr_scan_tracking (bool):  Default: True.
        is_favorite (bool):
        team_id (int | None | Unset):
        segment_key (str | Unset):
        webhook_url (str | Unset):
        integration_ga (str | Unset):
        integration_fb (str | Unset):
        integration_tt (str | Unset):
        integration_adroll (str | Unset):
        integration_gtm (str | Unset):
        ssl_cert_expiration_date (datetime.datetime | Unset):
        ssl_cert_installed_success (bool | Unset):
        domain_registration_id (int | Unset):
        user_id (int | Unset):
    """

    id: int
    hostname: str
    unicode_hostname: str
    state: GetApiDomainsResponse200ItemState
    created_at: datetime.datetime
    updated_at: datetime.datetime
    has_favicon: bool
    hide_referer: bool
    link_type: GetApiDomainsResponse200ItemLinkType
    cloaking: bool
    hide_visitor_ip: bool
    enable_ai: bool
    https_level: GetApiDomainsResponse200ItemHttpsLevel
    https_links: bool | None
    client_storage: GetApiDomainsResponse200ItemClientStorage
    case_sensitive: bool
    increment_counter: str
    robots: GetApiDomainsResponse200ItemRobots
    export_enabled: bool
    enable_conversion_tracking: bool
    is_favorite: bool
    qr_scan_tracking: bool = True
    team_id: int | None | Unset = UNSET
    segment_key: str | Unset = UNSET
    webhook_url: str | Unset = UNSET
    integration_ga: str | Unset = UNSET
    integration_fb: str | Unset = UNSET
    integration_tt: str | Unset = UNSET
    integration_adroll: str | Unset = UNSET
    integration_gtm: str | Unset = UNSET
    ssl_cert_expiration_date: datetime.datetime | Unset = UNSET
    ssl_cert_installed_success: bool | Unset = UNSET
    domain_registration_id: int | Unset = UNSET
    user_id: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        hostname = self.hostname

        unicode_hostname = self.unicode_hostname

        state = self.state.value

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        has_favicon = self.has_favicon

        hide_referer = self.hide_referer

        link_type = self.link_type.value

        cloaking = self.cloaking

        hide_visitor_ip = self.hide_visitor_ip

        enable_ai = self.enable_ai

        https_level = self.https_level.value

        https_links: bool | None
        https_links = self.https_links

        client_storage = self.client_storage.to_dict()

        case_sensitive = self.case_sensitive

        increment_counter = self.increment_counter

        robots = self.robots.value

        export_enabled = self.export_enabled

        enable_conversion_tracking = self.enable_conversion_tracking

        qr_scan_tracking = self.qr_scan_tracking

        is_favorite = self.is_favorite

        team_id: int | None | Unset
        if isinstance(self.team_id, Unset):
            team_id = UNSET
        else:
            team_id = self.team_id

        segment_key = self.segment_key

        webhook_url = self.webhook_url

        integration_ga = self.integration_ga

        integration_fb = self.integration_fb

        integration_tt = self.integration_tt

        integration_adroll = self.integration_adroll

        integration_gtm = self.integration_gtm

        ssl_cert_expiration_date: str | Unset = UNSET
        if not isinstance(self.ssl_cert_expiration_date, Unset):
            ssl_cert_expiration_date = self.ssl_cert_expiration_date.isoformat()

        ssl_cert_installed_success = self.ssl_cert_installed_success

        domain_registration_id = self.domain_registration_id

        user_id = self.user_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "hostname": hostname,
                "unicodeHostname": unicode_hostname,
                "state": state,
                "createdAt": created_at,
                "updatedAt": updated_at,
                "hasFavicon": has_favicon,
                "hideReferer": hide_referer,
                "linkType": link_type,
                "cloaking": cloaking,
                "hideVisitorIp": hide_visitor_ip,
                "enableAI": enable_ai,
                "httpsLevel": https_level,
                "httpsLinks": https_links,
                "clientStorage": client_storage,
                "caseSensitive": case_sensitive,
                "incrementCounter": increment_counter,
                "robots": robots,
                "exportEnabled": export_enabled,
                "enableConversionTracking": enable_conversion_tracking,
                "qrScanTracking": qr_scan_tracking,
                "isFavorite": is_favorite,
            }
        )
        if team_id is not UNSET:
            field_dict["TeamId"] = team_id
        if segment_key is not UNSET:
            field_dict["segmentKey"] = segment_key
        if webhook_url is not UNSET:
            field_dict["webhookURL"] = webhook_url
        if integration_ga is not UNSET:
            field_dict["integrationGA"] = integration_ga
        if integration_fb is not UNSET:
            field_dict["integrationFB"] = integration_fb
        if integration_tt is not UNSET:
            field_dict["integrationTT"] = integration_tt
        if integration_adroll is not UNSET:
            field_dict["integrationAdroll"] = integration_adroll
        if integration_gtm is not UNSET:
            field_dict["integrationGTM"] = integration_gtm
        if ssl_cert_expiration_date is not UNSET:
            field_dict["sslCertExpirationDate"] = ssl_cert_expiration_date
        if ssl_cert_installed_success is not UNSET:
            field_dict["sslCertInstalledSuccess"] = ssl_cert_installed_success
        if domain_registration_id is not UNSET:
            field_dict["domainRegistrationId"] = domain_registration_id
        if user_id is not UNSET:
            field_dict["UserId"] = user_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_api_domains_response_200_item_client_storage import GetApiDomainsResponse200ItemClientStorage

        d = dict(src_dict)
        id = d.pop("id")

        hostname = d.pop("hostname")

        unicode_hostname = d.pop("unicodeHostname")

        state = GetApiDomainsResponse200ItemState(d.pop("state"))

        created_at = isoparse(d.pop("createdAt"))

        updated_at = isoparse(d.pop("updatedAt"))

        has_favicon = d.pop("hasFavicon")

        hide_referer = d.pop("hideReferer")

        link_type = GetApiDomainsResponse200ItemLinkType(d.pop("linkType"))

        cloaking = d.pop("cloaking")

        hide_visitor_ip = d.pop("hideVisitorIp")

        enable_ai = d.pop("enableAI")

        https_level = GetApiDomainsResponse200ItemHttpsLevel(d.pop("httpsLevel"))

        def _parse_https_links(data: object) -> bool | None:
            if data is None:
                return data
            return cast(bool | None, data)

        https_links = _parse_https_links(d.pop("httpsLinks"))

        client_storage = GetApiDomainsResponse200ItemClientStorage.from_dict(d.pop("clientStorage"))

        case_sensitive = d.pop("caseSensitive")

        increment_counter = d.pop("incrementCounter")

        robots = GetApiDomainsResponse200ItemRobots(d.pop("robots"))

        export_enabled = d.pop("exportEnabled")

        enable_conversion_tracking = d.pop("enableConversionTracking")

        qr_scan_tracking = d.pop("qrScanTracking")

        is_favorite = d.pop("isFavorite")

        def _parse_team_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        team_id = _parse_team_id(d.pop("TeamId", UNSET))

        segment_key = d.pop("segmentKey", UNSET)

        webhook_url = d.pop("webhookURL", UNSET)

        integration_ga = d.pop("integrationGA", UNSET)

        integration_fb = d.pop("integrationFB", UNSET)

        integration_tt = d.pop("integrationTT", UNSET)

        integration_adroll = d.pop("integrationAdroll", UNSET)

        integration_gtm = d.pop("integrationGTM", UNSET)

        _ssl_cert_expiration_date = d.pop("sslCertExpirationDate", UNSET)
        ssl_cert_expiration_date: datetime.datetime | Unset
        if isinstance(_ssl_cert_expiration_date, Unset):
            ssl_cert_expiration_date = UNSET
        else:
            ssl_cert_expiration_date = isoparse(_ssl_cert_expiration_date)

        ssl_cert_installed_success = d.pop("sslCertInstalledSuccess", UNSET)

        domain_registration_id = d.pop("domainRegistrationId", UNSET)

        user_id = d.pop("UserId", UNSET)

        get_api_domains_response_200_item = cls(
            id=id,
            hostname=hostname,
            unicode_hostname=unicode_hostname,
            state=state,
            created_at=created_at,
            updated_at=updated_at,
            has_favicon=has_favicon,
            hide_referer=hide_referer,
            link_type=link_type,
            cloaking=cloaking,
            hide_visitor_ip=hide_visitor_ip,
            enable_ai=enable_ai,
            https_level=https_level,
            https_links=https_links,
            client_storage=client_storage,
            case_sensitive=case_sensitive,
            increment_counter=increment_counter,
            robots=robots,
            export_enabled=export_enabled,
            enable_conversion_tracking=enable_conversion_tracking,
            qr_scan_tracking=qr_scan_tracking,
            is_favorite=is_favorite,
            team_id=team_id,
            segment_key=segment_key,
            webhook_url=webhook_url,
            integration_ga=integration_ga,
            integration_fb=integration_fb,
            integration_tt=integration_tt,
            integration_adroll=integration_adroll,
            integration_gtm=integration_gtm,
            ssl_cert_expiration_date=ssl_cert_expiration_date,
            ssl_cert_installed_success=ssl_cert_installed_success,
            domain_registration_id=domain_registration_id,
            user_id=user_id,
        )

        get_api_domains_response_200_item.additional_properties = d
        return get_api_domains_response_200_item

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
