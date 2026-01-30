from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.post_domains_settings_domain_id_body_https_level import PostDomainsSettingsDomainIdBodyHttpsLevel
from ..models.post_domains_settings_domain_id_body_link_type import PostDomainsSettingsDomainIdBodyLinkType
from ..models.post_domains_settings_domain_id_body_robots import PostDomainsSettingsDomainIdBodyRobots
from ..models.post_domains_settings_domain_id_body_webhook_url_type_1 import (
    PostDomainsSettingsDomainIdBodyWebhookURLType1,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.post_domains_settings_domain_id_body_client_storage import (
        PostDomainsSettingsDomainIdBodyClientStorage,
    )


T = TypeVar("T", bound="PostDomainsSettingsDomainIdBody")


@_attrs_define
class PostDomainsSettingsDomainIdBody:
    """
    Attributes:
        https_level (PostDomainsSettingsDomainIdBodyHttpsLevel | Unset):
        robots (PostDomainsSettingsDomainIdBodyRobots | Unset):
        segment_key (None | str | Unset):
        link_type (PostDomainsSettingsDomainIdBodyLinkType | Unset):
        cloaking (bool | Unset): Enable cloaking for all links on the domain
        hide_referer (bool | Unset):
        hide_visitor_ip (bool | Unset): Don't store visitor IPs in our database
        https_links (bool | None | Unset): Set to null to reissue a certificate
        webhook_url (None | PostDomainsSettingsDomainIdBodyWebhookURLType1 | str | Unset):
        integration_ga (None | str | Unset):
        integration_fb (None | str | Unset):
        integration_tt (None | str | Unset):
        integration_adroll (None | str | Unset):
        enable_conversion_tracking (bool | Unset):
        qr_scan_tracking (bool | Unset):  Default: True.
        integration_gtm (None | str | Unset):  Example: G-1234567.
        client_storage (PostDomainsSettingsDomainIdBodyClientStorage | Unset): For internal use
        purge_expired_links (bool | Unset): [DEPRECATED] do not use
        enable_ai (bool | Unset):
        case_sensitive (bool | Unset): Enable case sensitivity for short links
    """

    https_level: PostDomainsSettingsDomainIdBodyHttpsLevel | Unset = UNSET
    robots: PostDomainsSettingsDomainIdBodyRobots | Unset = UNSET
    segment_key: None | str | Unset = UNSET
    link_type: PostDomainsSettingsDomainIdBodyLinkType | Unset = UNSET
    cloaking: bool | Unset = UNSET
    hide_referer: bool | Unset = UNSET
    hide_visitor_ip: bool | Unset = UNSET
    https_links: bool | None | Unset = UNSET
    webhook_url: None | PostDomainsSettingsDomainIdBodyWebhookURLType1 | str | Unset = UNSET
    integration_ga: None | str | Unset = UNSET
    integration_fb: None | str | Unset = UNSET
    integration_tt: None | str | Unset = UNSET
    integration_adroll: None | str | Unset = UNSET
    enable_conversion_tracking: bool | Unset = UNSET
    qr_scan_tracking: bool | Unset = True
    integration_gtm: None | str | Unset = UNSET
    client_storage: PostDomainsSettingsDomainIdBodyClientStorage | Unset = UNSET
    purge_expired_links: bool | Unset = UNSET
    enable_ai: bool | Unset = UNSET
    case_sensitive: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        https_level: str | Unset = UNSET
        if not isinstance(self.https_level, Unset):
            https_level = self.https_level.value

        robots: str | Unset = UNSET
        if not isinstance(self.robots, Unset):
            robots = self.robots.value

        segment_key: None | str | Unset
        if isinstance(self.segment_key, Unset):
            segment_key = UNSET
        else:
            segment_key = self.segment_key

        link_type: str | Unset = UNSET
        if not isinstance(self.link_type, Unset):
            link_type = self.link_type.value

        cloaking = self.cloaking

        hide_referer = self.hide_referer

        hide_visitor_ip = self.hide_visitor_ip

        https_links: bool | None | Unset
        if isinstance(self.https_links, Unset):
            https_links = UNSET
        else:
            https_links = self.https_links

        webhook_url: None | str | Unset
        if isinstance(self.webhook_url, Unset):
            webhook_url = UNSET
        elif isinstance(self.webhook_url, PostDomainsSettingsDomainIdBodyWebhookURLType1):
            webhook_url = self.webhook_url.value
        else:
            webhook_url = self.webhook_url

        integration_ga: None | str | Unset
        if isinstance(self.integration_ga, Unset):
            integration_ga = UNSET
        else:
            integration_ga = self.integration_ga

        integration_fb: None | str | Unset
        if isinstance(self.integration_fb, Unset):
            integration_fb = UNSET
        else:
            integration_fb = self.integration_fb

        integration_tt: None | str | Unset
        if isinstance(self.integration_tt, Unset):
            integration_tt = UNSET
        else:
            integration_tt = self.integration_tt

        integration_adroll: None | str | Unset
        if isinstance(self.integration_adroll, Unset):
            integration_adroll = UNSET
        else:
            integration_adroll = self.integration_adroll

        enable_conversion_tracking = self.enable_conversion_tracking

        qr_scan_tracking = self.qr_scan_tracking

        integration_gtm: None | str | Unset
        if isinstance(self.integration_gtm, Unset):
            integration_gtm = UNSET
        else:
            integration_gtm = self.integration_gtm

        client_storage: dict[str, Any] | Unset = UNSET
        if not isinstance(self.client_storage, Unset):
            client_storage = self.client_storage.to_dict()

        purge_expired_links = self.purge_expired_links

        enable_ai = self.enable_ai

        case_sensitive = self.case_sensitive

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if https_level is not UNSET:
            field_dict["httpsLevel"] = https_level
        if robots is not UNSET:
            field_dict["robots"] = robots
        if segment_key is not UNSET:
            field_dict["segmentKey"] = segment_key
        if link_type is not UNSET:
            field_dict["linkType"] = link_type
        if cloaking is not UNSET:
            field_dict["cloaking"] = cloaking
        if hide_referer is not UNSET:
            field_dict["hideReferer"] = hide_referer
        if hide_visitor_ip is not UNSET:
            field_dict["hideVisitorIp"] = hide_visitor_ip
        if https_links is not UNSET:
            field_dict["httpsLinks"] = https_links
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
        if enable_conversion_tracking is not UNSET:
            field_dict["enableConversionTracking"] = enable_conversion_tracking
        if qr_scan_tracking is not UNSET:
            field_dict["qrScanTracking"] = qr_scan_tracking
        if integration_gtm is not UNSET:
            field_dict["integrationGTM"] = integration_gtm
        if client_storage is not UNSET:
            field_dict["clientStorage"] = client_storage
        if purge_expired_links is not UNSET:
            field_dict["purgeExpiredLinks"] = purge_expired_links
        if enable_ai is not UNSET:
            field_dict["enableAI"] = enable_ai
        if case_sensitive is not UNSET:
            field_dict["caseSensitive"] = case_sensitive

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_domains_settings_domain_id_body_client_storage import (
            PostDomainsSettingsDomainIdBodyClientStorage,
        )

        d = dict(src_dict)
        _https_level = d.pop("httpsLevel", UNSET)
        https_level: PostDomainsSettingsDomainIdBodyHttpsLevel | Unset
        if isinstance(_https_level, Unset):
            https_level = UNSET
        else:
            https_level = PostDomainsSettingsDomainIdBodyHttpsLevel(_https_level)

        _robots = d.pop("robots", UNSET)
        robots: PostDomainsSettingsDomainIdBodyRobots | Unset
        if isinstance(_robots, Unset):
            robots = UNSET
        else:
            robots = PostDomainsSettingsDomainIdBodyRobots(_robots)

        def _parse_segment_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        segment_key = _parse_segment_key(d.pop("segmentKey", UNSET))

        _link_type = d.pop("linkType", UNSET)
        link_type: PostDomainsSettingsDomainIdBodyLinkType | Unset
        if isinstance(_link_type, Unset):
            link_type = UNSET
        else:
            link_type = PostDomainsSettingsDomainIdBodyLinkType(_link_type)

        cloaking = d.pop("cloaking", UNSET)

        hide_referer = d.pop("hideReferer", UNSET)

        hide_visitor_ip = d.pop("hideVisitorIp", UNSET)

        def _parse_https_links(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        https_links = _parse_https_links(d.pop("httpsLinks", UNSET))

        def _parse_webhook_url(data: object) -> None | PostDomainsSettingsDomainIdBodyWebhookURLType1 | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                webhook_url_type_1 = PostDomainsSettingsDomainIdBodyWebhookURLType1(data)

                return webhook_url_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PostDomainsSettingsDomainIdBodyWebhookURLType1 | str | Unset, data)

        webhook_url = _parse_webhook_url(d.pop("webhookURL", UNSET))

        def _parse_integration_ga(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        integration_ga = _parse_integration_ga(d.pop("integrationGA", UNSET))

        def _parse_integration_fb(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        integration_fb = _parse_integration_fb(d.pop("integrationFB", UNSET))

        def _parse_integration_tt(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        integration_tt = _parse_integration_tt(d.pop("integrationTT", UNSET))

        def _parse_integration_adroll(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        integration_adroll = _parse_integration_adroll(d.pop("integrationAdroll", UNSET))

        enable_conversion_tracking = d.pop("enableConversionTracking", UNSET)

        qr_scan_tracking = d.pop("qrScanTracking", UNSET)

        def _parse_integration_gtm(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        integration_gtm = _parse_integration_gtm(d.pop("integrationGTM", UNSET))

        _client_storage = d.pop("clientStorage", UNSET)
        client_storage: PostDomainsSettingsDomainIdBodyClientStorage | Unset
        if isinstance(_client_storage, Unset):
            client_storage = UNSET
        else:
            client_storage = PostDomainsSettingsDomainIdBodyClientStorage.from_dict(_client_storage)

        purge_expired_links = d.pop("purgeExpiredLinks", UNSET)

        enable_ai = d.pop("enableAI", UNSET)

        case_sensitive = d.pop("caseSensitive", UNSET)

        post_domains_settings_domain_id_body = cls(
            https_level=https_level,
            robots=robots,
            segment_key=segment_key,
            link_type=link_type,
            cloaking=cloaking,
            hide_referer=hide_referer,
            hide_visitor_ip=hide_visitor_ip,
            https_links=https_links,
            webhook_url=webhook_url,
            integration_ga=integration_ga,
            integration_fb=integration_fb,
            integration_tt=integration_tt,
            integration_adroll=integration_adroll,
            enable_conversion_tracking=enable_conversion_tracking,
            qr_scan_tracking=qr_scan_tracking,
            integration_gtm=integration_gtm,
            client_storage=client_storage,
            purge_expired_links=purge_expired_links,
            enable_ai=enable_ai,
            case_sensitive=case_sensitive,
        )

        post_domains_settings_domain_id_body.additional_properties = d
        return post_domains_settings_domain_id_body

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
