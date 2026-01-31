from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_status_body_shipment import GetStatusBodyShipment


T = TypeVar("T", bound="GetStatusBody")


@_attrs_define
class GetStatusBody:
    """
    Attributes:
        shipment (GetStatusBodyShipment | Unset):
        channel (str | Unset): The channel through which the shipments have been made Example: shopify.
        date_from (str | Unset): The starting date for the shipment status event period. Example: 2023-01-16 15:30:11.
        date_to (str | Unset): The end date for the shipment period. Example: 2023-03-16 15:30:11.
        is_incremental (bool | Unset): **true:** Shows which status events have been received.
            **false:** Shows all status events Default: False.
    """

    shipment: GetStatusBodyShipment | Unset = UNSET
    channel: str | Unset = UNSET
    date_from: str | Unset = UNSET
    date_to: str | Unset = UNSET
    is_incremental: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        shipment: dict[str, Any] | Unset = UNSET
        if not isinstance(self.shipment, Unset):
            shipment = self.shipment.to_dict()

        channel = self.channel

        date_from = self.date_from

        date_to = self.date_to

        is_incremental = self.is_incremental

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if shipment is not UNSET:
            field_dict["shipment"] = shipment
        if channel is not UNSET:
            field_dict["channel"] = channel
        if date_from is not UNSET:
            field_dict["dateFrom"] = date_from
        if date_to is not UNSET:
            field_dict["dateTo"] = date_to
        if is_incremental is not UNSET:
            field_dict["isIncremental"] = is_incremental

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_status_body_shipment import GetStatusBodyShipment

        d = dict(src_dict)
        _shipment = d.pop("shipment", UNSET)
        shipment: GetStatusBodyShipment | Unset
        if isinstance(_shipment, Unset):
            shipment = UNSET
        else:
            shipment = GetStatusBodyShipment.from_dict(_shipment)

        channel = d.pop("channel", UNSET)

        date_from = d.pop("dateFrom", UNSET)

        date_to = d.pop("dateTo", UNSET)

        is_incremental = d.pop("isIncremental", UNSET)

        get_status_body = cls(
            shipment=shipment,
            channel=channel,
            date_from=date_from,
            date_to=date_to,
            is_incremental=is_incremental,
        )

        get_status_body.additional_properties = d
        return get_status_body

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
