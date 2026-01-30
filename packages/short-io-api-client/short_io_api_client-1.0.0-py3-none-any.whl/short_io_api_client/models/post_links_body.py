from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.post_links_body_redirect_type import PostLinksBodyRedirectType
from ..types import UNSET, Unset

T = TypeVar("T", bound="PostLinksBody")


@_attrs_define
class PostLinksBody:
    """
    Attributes:
        original_url (str): Original URL
        domain (str): Domain hostname
        cloaking (bool | Unset): Cloaking
        password (str | Unset): Link password
        redirect_type (PostLinksBodyRedirectType | Unset): HTTP code for redirect
        expires_at (int | None | str | Unset): Link expiration date in milliseconds or ISO string
        expired_url (None | str | Unset): Expired URL
        title (str | Unset): Link title
        tags (list[str] | Unset): Array of link tags
        utm_source (str | Unset): set utm_source parameter to destination link
        utm_medium (str | Unset): set utm_medium parameter to destination link
        utm_campaign (str | Unset): set utm_campaign parameter to destination link
        utm_term (str | Unset): set utm_term parameter to destination link
        utm_content (str | Unset): set utm_content parameter to destination link
        ttl (int | None | str | Unset): Time to live in milliseconds or ISO string
        path (None | str | Unset): Link slug
        android_url (None | str | Unset): Android URL
        iphone_url (None | str | Unset): iPhone URL
        created_at (int | None | str | Unset): Link creation date in milliseconds
        clicks_limit (int | None | Unset): disable link after specified number of clicks
        password_contact (bool | None | Unset): Provide your email to users to get a password
        skip_qs (bool | Unset): Skip query string merging Default: False.
        archived (bool | Unset): Link is archived Default: False.
        split_url (None | str | Unset): Split URL
        split_percent (int | None | Unset): Split URL percentage
        integration_adroll (None | str | Unset): Adroll integration
        integration_fb (None | str | Unset): Facebook integration
        integration_tt (None | str | Unset): TikTok integration
        integration_ga (None | str | Unset): Google Analytics integration
        integration_gtm (None | str | Unset): Google Tag Manager integration
        allow_duplicates (bool | Unset): Allow duplicates Default: False.
        folder_id (str | Unset): Folder ID
    """

    original_url: str
    domain: str
    cloaking: bool | Unset = UNSET
    password: str | Unset = UNSET
    redirect_type: PostLinksBodyRedirectType | Unset = UNSET
    expires_at: int | None | str | Unset = UNSET
    expired_url: None | str | Unset = UNSET
    title: str | Unset = UNSET
    tags: list[str] | Unset = UNSET
    utm_source: str | Unset = UNSET
    utm_medium: str | Unset = UNSET
    utm_campaign: str | Unset = UNSET
    utm_term: str | Unset = UNSET
    utm_content: str | Unset = UNSET
    ttl: int | None | str | Unset = UNSET
    path: None | str | Unset = UNSET
    android_url: None | str | Unset = UNSET
    iphone_url: None | str | Unset = UNSET
    created_at: int | None | str | Unset = UNSET
    clicks_limit: int | None | Unset = UNSET
    password_contact: bool | None | Unset = UNSET
    skip_qs: bool | Unset = False
    archived: bool | Unset = False
    split_url: None | str | Unset = UNSET
    split_percent: int | None | Unset = UNSET
    integration_adroll: None | str | Unset = UNSET
    integration_fb: None | str | Unset = UNSET
    integration_tt: None | str | Unset = UNSET
    integration_ga: None | str | Unset = UNSET
    integration_gtm: None | str | Unset = UNSET
    allow_duplicates: bool | Unset = False
    folder_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        original_url = self.original_url

        domain = self.domain

        cloaking = self.cloaking

        password = self.password

        redirect_type: int | Unset = UNSET
        if not isinstance(self.redirect_type, Unset):
            redirect_type = self.redirect_type.value

        expires_at: int | None | str | Unset
        if isinstance(self.expires_at, Unset):
            expires_at = UNSET
        else:
            expires_at = self.expires_at

        expired_url: None | str | Unset
        if isinstance(self.expired_url, Unset):
            expired_url = UNSET
        else:
            expired_url = self.expired_url

        title = self.title

        tags: list[str] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags

        utm_source = self.utm_source

        utm_medium = self.utm_medium

        utm_campaign = self.utm_campaign

        utm_term = self.utm_term

        utm_content = self.utm_content

        ttl: int | None | str | Unset
        if isinstance(self.ttl, Unset):
            ttl = UNSET
        else:
            ttl = self.ttl

        path: None | str | Unset
        if isinstance(self.path, Unset):
            path = UNSET
        else:
            path = self.path

        android_url: None | str | Unset
        if isinstance(self.android_url, Unset):
            android_url = UNSET
        else:
            android_url = self.android_url

        iphone_url: None | str | Unset
        if isinstance(self.iphone_url, Unset):
            iphone_url = UNSET
        else:
            iphone_url = self.iphone_url

        created_at: int | None | str | Unset
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        else:
            created_at = self.created_at

        clicks_limit: int | None | Unset
        if isinstance(self.clicks_limit, Unset):
            clicks_limit = UNSET
        else:
            clicks_limit = self.clicks_limit

        password_contact: bool | None | Unset
        if isinstance(self.password_contact, Unset):
            password_contact = UNSET
        else:
            password_contact = self.password_contact

        skip_qs = self.skip_qs

        archived = self.archived

        split_url: None | str | Unset
        if isinstance(self.split_url, Unset):
            split_url = UNSET
        else:
            split_url = self.split_url

        split_percent: int | None | Unset
        if isinstance(self.split_percent, Unset):
            split_percent = UNSET
        else:
            split_percent = self.split_percent

        integration_adroll: None | str | Unset
        if isinstance(self.integration_adroll, Unset):
            integration_adroll = UNSET
        else:
            integration_adroll = self.integration_adroll

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

        integration_ga: None | str | Unset
        if isinstance(self.integration_ga, Unset):
            integration_ga = UNSET
        else:
            integration_ga = self.integration_ga

        integration_gtm: None | str | Unset
        if isinstance(self.integration_gtm, Unset):
            integration_gtm = UNSET
        else:
            integration_gtm = self.integration_gtm

        allow_duplicates = self.allow_duplicates

        folder_id = self.folder_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "originalURL": original_url,
                "domain": domain,
            }
        )
        if cloaking is not UNSET:
            field_dict["cloaking"] = cloaking
        if password is not UNSET:
            field_dict["password"] = password
        if redirect_type is not UNSET:
            field_dict["redirectType"] = redirect_type
        if expires_at is not UNSET:
            field_dict["expiresAt"] = expires_at
        if expired_url is not UNSET:
            field_dict["expiredURL"] = expired_url
        if title is not UNSET:
            field_dict["title"] = title
        if tags is not UNSET:
            field_dict["tags"] = tags
        if utm_source is not UNSET:
            field_dict["utmSource"] = utm_source
        if utm_medium is not UNSET:
            field_dict["utmMedium"] = utm_medium
        if utm_campaign is not UNSET:
            field_dict["utmCampaign"] = utm_campaign
        if utm_term is not UNSET:
            field_dict["utmTerm"] = utm_term
        if utm_content is not UNSET:
            field_dict["utmContent"] = utm_content
        if ttl is not UNSET:
            field_dict["ttl"] = ttl
        if path is not UNSET:
            field_dict["path"] = path
        if android_url is not UNSET:
            field_dict["androidURL"] = android_url
        if iphone_url is not UNSET:
            field_dict["iphoneURL"] = iphone_url
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if clicks_limit is not UNSET:
            field_dict["clicksLimit"] = clicks_limit
        if password_contact is not UNSET:
            field_dict["passwordContact"] = password_contact
        if skip_qs is not UNSET:
            field_dict["skipQS"] = skip_qs
        if archived is not UNSET:
            field_dict["archived"] = archived
        if split_url is not UNSET:
            field_dict["splitURL"] = split_url
        if split_percent is not UNSET:
            field_dict["splitPercent"] = split_percent
        if integration_adroll is not UNSET:
            field_dict["integrationAdroll"] = integration_adroll
        if integration_fb is not UNSET:
            field_dict["integrationFB"] = integration_fb
        if integration_tt is not UNSET:
            field_dict["integrationTT"] = integration_tt
        if integration_ga is not UNSET:
            field_dict["integrationGA"] = integration_ga
        if integration_gtm is not UNSET:
            field_dict["integrationGTM"] = integration_gtm
        if allow_duplicates is not UNSET:
            field_dict["allowDuplicates"] = allow_duplicates
        if folder_id is not UNSET:
            field_dict["folderId"] = folder_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        original_url = d.pop("originalURL")

        domain = d.pop("domain")

        cloaking = d.pop("cloaking", UNSET)

        password = d.pop("password", UNSET)

        _redirect_type = d.pop("redirectType", UNSET)
        redirect_type: PostLinksBodyRedirectType | Unset
        if isinstance(_redirect_type, Unset):
            redirect_type = UNSET
        else:
            redirect_type = PostLinksBodyRedirectType(_redirect_type)

        def _parse_expires_at(data: object) -> int | None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | str | Unset, data)

        expires_at = _parse_expires_at(d.pop("expiresAt", UNSET))

        def _parse_expired_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        expired_url = _parse_expired_url(d.pop("expiredURL", UNSET))

        title = d.pop("title", UNSET)

        tags = cast(list[str], d.pop("tags", UNSET))

        utm_source = d.pop("utmSource", UNSET)

        utm_medium = d.pop("utmMedium", UNSET)

        utm_campaign = d.pop("utmCampaign", UNSET)

        utm_term = d.pop("utmTerm", UNSET)

        utm_content = d.pop("utmContent", UNSET)

        def _parse_ttl(data: object) -> int | None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | str | Unset, data)

        ttl = _parse_ttl(d.pop("ttl", UNSET))

        def _parse_path(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        path = _parse_path(d.pop("path", UNSET))

        def _parse_android_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        android_url = _parse_android_url(d.pop("androidURL", UNSET))

        def _parse_iphone_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        iphone_url = _parse_iphone_url(d.pop("iphoneURL", UNSET))

        def _parse_created_at(data: object) -> int | None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | str | Unset, data)

        created_at = _parse_created_at(d.pop("createdAt", UNSET))

        def _parse_clicks_limit(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        clicks_limit = _parse_clicks_limit(d.pop("clicksLimit", UNSET))

        def _parse_password_contact(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        password_contact = _parse_password_contact(d.pop("passwordContact", UNSET))

        skip_qs = d.pop("skipQS", UNSET)

        archived = d.pop("archived", UNSET)

        def _parse_split_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        split_url = _parse_split_url(d.pop("splitURL", UNSET))

        def _parse_split_percent(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        split_percent = _parse_split_percent(d.pop("splitPercent", UNSET))

        def _parse_integration_adroll(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        integration_adroll = _parse_integration_adroll(d.pop("integrationAdroll", UNSET))

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

        def _parse_integration_ga(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        integration_ga = _parse_integration_ga(d.pop("integrationGA", UNSET))

        def _parse_integration_gtm(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        integration_gtm = _parse_integration_gtm(d.pop("integrationGTM", UNSET))

        allow_duplicates = d.pop("allowDuplicates", UNSET)

        folder_id = d.pop("folderId", UNSET)

        post_links_body = cls(
            original_url=original_url,
            domain=domain,
            cloaking=cloaking,
            password=password,
            redirect_type=redirect_type,
            expires_at=expires_at,
            expired_url=expired_url,
            title=title,
            tags=tags,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
            utm_term=utm_term,
            utm_content=utm_content,
            ttl=ttl,
            path=path,
            android_url=android_url,
            iphone_url=iphone_url,
            created_at=created_at,
            clicks_limit=clicks_limit,
            password_contact=password_contact,
            skip_qs=skip_qs,
            archived=archived,
            split_url=split_url,
            split_percent=split_percent,
            integration_adroll=integration_adroll,
            integration_fb=integration_fb,
            integration_tt=integration_tt,
            integration_ga=integration_ga,
            integration_gtm=integration_gtm,
            allow_duplicates=allow_duplicates,
            folder_id=folder_id,
        )

        post_links_body.additional_properties = d
        return post_links_body

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
