from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.email_domain_status import EmailDomainStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.dns_record import DnsRecord


T = TypeVar("T", bound="EmailDomain")


@_attrs_define
class EmailDomain:
    """Email domain with verification status.

    Attributes:
        domain (str): Domain name
        status (EmailDomainStatus): Email domain verification status.
        created_at (str): When domain was added
        from_name (None | str | Unset): Default sender name
        dns_records (list[DnsRecord] | Unset): DNS records to add
        verified_at (None | str | Unset): When domain was verified
    """

    domain: str
    status: EmailDomainStatus
    created_at: str
    from_name: None | str | Unset = UNSET
    dns_records: list[DnsRecord] | Unset = UNSET
    verified_at: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        domain = self.domain

        status = self.status.value

        created_at = self.created_at

        from_name: None | str | Unset
        if isinstance(self.from_name, Unset):
            from_name = UNSET
        else:
            from_name = self.from_name

        dns_records: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.dns_records, Unset):
            dns_records = []
            for dns_records_item_data in self.dns_records:
                dns_records_item = dns_records_item_data.to_dict()
                dns_records.append(dns_records_item)

        verified_at: None | str | Unset
        if isinstance(self.verified_at, Unset):
            verified_at = UNSET
        else:
            verified_at = self.verified_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "domain": domain,
                "status": status,
                "created_at": created_at,
            }
        )
        if from_name is not UNSET:
            field_dict["from_name"] = from_name
        if dns_records is not UNSET:
            field_dict["dns_records"] = dns_records
        if verified_at is not UNSET:
            field_dict["verified_at"] = verified_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dns_record import DnsRecord

        d = dict(src_dict)
        domain = d.pop("domain")

        status = EmailDomainStatus(d.pop("status"))

        created_at = d.pop("created_at")

        def _parse_from_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        from_name = _parse_from_name(d.pop("from_name", UNSET))

        _dns_records = d.pop("dns_records", UNSET)
        dns_records: list[DnsRecord] | Unset = UNSET
        if _dns_records is not UNSET:
            dns_records = []
            for dns_records_item_data in _dns_records:
                dns_records_item = DnsRecord.from_dict(dns_records_item_data)

                dns_records.append(dns_records_item)

        def _parse_verified_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        verified_at = _parse_verified_at(d.pop("verified_at", UNSET))

        email_domain = cls(
            domain=domain,
            status=status,
            created_at=created_at,
            from_name=from_name,
            dns_records=dns_records,
            verified_at=verified_at,
        )

        email_domain.additional_properties = d
        return email_domain

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
