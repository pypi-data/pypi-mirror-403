from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.insert_shipments_response_200_options_item import InsertShipmentsResponse200OptionsItem
    from ..models.insert_shipments_response_200_shipments_item import InsertShipmentsResponse200ShipmentsItem


T = TypeVar("T", bound="InsertShipmentsResponse200")


@_attrs_define
class InsertShipmentsResponse200:
    """
    Attributes:
        status (str | Unset):
        code (int | Unset):
        message (str | Unset):
        total_buy (int | Unset):
        total_sell (int | Unset):
        longest_deliverydate (bool | Unset):
        options (list[InsertShipmentsResponse200OptionsItem] | Unset):
        shipments (list[InsertShipmentsResponse200ShipmentsItem] | Unset):
    """

    status: str | Unset = UNSET
    code: int | Unset = UNSET
    message: str | Unset = UNSET
    total_buy: int | Unset = UNSET
    total_sell: int | Unset = UNSET
    longest_deliverydate: bool | Unset = UNSET
    options: list[InsertShipmentsResponse200OptionsItem] | Unset = UNSET
    shipments: list[InsertShipmentsResponse200ShipmentsItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        code = self.code

        message = self.message

        total_buy = self.total_buy

        total_sell = self.total_sell

        longest_deliverydate = self.longest_deliverydate

        options: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.options, Unset):
            options = []
            for options_item_data in self.options:
                options_item = options_item_data.to_dict()
                options.append(options_item)

        shipments: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.shipments, Unset):
            shipments = []
            for shipments_item_data in self.shipments:
                shipments_item = shipments_item_data.to_dict()
                shipments.append(shipments_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if status is not UNSET:
            field_dict["status"] = status
        if code is not UNSET:
            field_dict["code"] = code
        if message is not UNSET:
            field_dict["message"] = message
        if total_buy is not UNSET:
            field_dict["totalBuy"] = total_buy
        if total_sell is not UNSET:
            field_dict["totalSell"] = total_sell
        if longest_deliverydate is not UNSET:
            field_dict["longestDeliverydate"] = longest_deliverydate
        if options is not UNSET:
            field_dict["options"] = options
        if shipments is not UNSET:
            field_dict["shipments"] = shipments

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.insert_shipments_response_200_options_item import InsertShipmentsResponse200OptionsItem
        from ..models.insert_shipments_response_200_shipments_item import InsertShipmentsResponse200ShipmentsItem

        d = dict(src_dict)
        status = d.pop("status", UNSET)

        code = d.pop("code", UNSET)

        message = d.pop("message", UNSET)

        total_buy = d.pop("totalBuy", UNSET)

        total_sell = d.pop("totalSell", UNSET)

        longest_deliverydate = d.pop("longestDeliverydate", UNSET)

        _options = d.pop("options", UNSET)
        options: list[InsertShipmentsResponse200OptionsItem] | Unset = UNSET
        if _options is not UNSET:
            options = []
            for options_item_data in _options:
                options_item = InsertShipmentsResponse200OptionsItem.from_dict(options_item_data)

                options.append(options_item)

        _shipments = d.pop("shipments", UNSET)
        shipments: list[InsertShipmentsResponse200ShipmentsItem] | Unset = UNSET
        if _shipments is not UNSET:
            shipments = []
            for shipments_item_data in _shipments:
                shipments_item = InsertShipmentsResponse200ShipmentsItem.from_dict(shipments_item_data)

                shipments.append(shipments_item)

        insert_shipments_response_200 = cls(
            status=status,
            code=code,
            message=message,
            total_buy=total_buy,
            total_sell=total_sell,
            longest_deliverydate=longest_deliverydate,
            options=options,
            shipments=shipments,
        )

        insert_shipments_response_200.additional_properties = d
        return insert_shipments_response_200

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
