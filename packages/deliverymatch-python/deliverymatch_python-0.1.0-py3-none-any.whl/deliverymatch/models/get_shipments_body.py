from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.get_shipments_body_status import GetShipmentsBodyStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="GetShipmentsBody")


@_attrs_define
class GetShipmentsBody:
    """
    Attributes:
        date_from (str): Filter from this date Example: 2022-09-04.
        date_to (str): Filter till this date Example: 2022-09-04.
        status (GetShipmentsBodyStatus | Unset): Filter the shipments by shipment status
        channel (str | Unset): Name of the channel Example: WEBSHOPNL.
    """

    date_from: str
    date_to: str
    status: GetShipmentsBodyStatus | Unset = UNSET
    channel: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        date_from = self.date_from

        date_to = self.date_to

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        channel = self.channel

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dateFrom": date_from,
                "dateTo": date_to,
            }
        )
        if status is not UNSET:
            field_dict["status"] = status
        if channel is not UNSET:
            field_dict["channel"] = channel

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        date_from = d.pop("dateFrom")

        date_to = d.pop("dateTo")

        _status = d.pop("status", UNSET)
        status: GetShipmentsBodyStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = GetShipmentsBodyStatus(_status)

        channel = d.pop("channel", UNSET)

        get_shipments_body = cls(
            date_from=date_from,
            date_to=date_to,
            status=status,
            channel=channel,
        )

        get_shipments_body.additional_properties = d
        return get_shipments_body

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
