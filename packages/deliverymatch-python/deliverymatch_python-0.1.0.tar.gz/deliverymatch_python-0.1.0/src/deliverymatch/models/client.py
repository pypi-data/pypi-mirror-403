from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.client_action import ClientAction
from ..models.client_method import ClientMethod
from ..types import UNSET, Unset

T = TypeVar("T", bound="Client")


@_attrs_define
class Client:
    """General information about the client and selected options

    Attributes:
        id (int | Unset): Your unique client ID supplied to you by DeliveryMatch, contains 3 numbers Example: 123.
        channel (str | Unset): Name of the order source (saleschannel) Example: Shopify.
        callback (str | Unset): Callback URL invoked when the shipment is updated. E.g. when shipment is delivered
            Example: https://api.company.com/orderupdate/order/ORD123.
        action (ClientAction | Unset): Via action the following values are possible:
            show: Request for just showing the shipping options the DeliveryMatch API

            save: Request for saving the shipment in DeliveryMatch, this does not return shipping options

            select: Request for selecting the most profitable method in the DeliveryMatch API, force a specific method via
            the ‘method’ key

            book: Request for booking the shipment in DeliveryMatch, this does return the shipping label(s) and track and
            trace URL

            print: Request for booking the shipment in DeliveryMatch and directly print the shipping labels via your label
            printer. This only works when a printnode user is set up in de DeliveryMatch UI. Forcing a specific printer can
            be done via the key ‘printerchannel’ in the object Shipment

            returnmail: This action is only possible for return shipments, and will book the shipment and email the label to
            the provided customer email address

            onlyshowcheapest = Request for showing the shipping options but let DeliveryMatch fiter on only the cheapest
            options per day-time

            selectbook: this action will force DeliveryMatch to reselect before booking

            selectprint: this action will force DeliveryMatch to reselect before booking and printing
        method (ClientMethod | Unset): Force a specific method filter in your request, the following values are
            possible:

            lowprice: show/book/select lowest price shipping option

            first: show/book/select fastest shipping option

            green: show/book/select most CO2 efficient shipping option
        filter_ (bool | Unset): Only return the least expensive shipping option for overlapping delivery time frames
            Default: False.
        transportlabel (bool | Unset): Returns a pick-transport label Default: False.
        copy (bool | Unset): If a shipment has already been booked, a copy of the original shipment will be made and any
            changes that are inserted with the new request are updated. Default: False.
    """

    id: int | Unset = UNSET
    channel: str | Unset = UNSET
    callback: str | Unset = UNSET
    action: ClientAction | Unset = UNSET
    method: ClientMethod | Unset = UNSET
    filter_: bool | Unset = False
    transportlabel: bool | Unset = False
    copy: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        channel = self.channel

        callback = self.callback

        action: str | Unset = UNSET
        if not isinstance(self.action, Unset):
            action = self.action.value

        method: str | Unset = UNSET
        if not isinstance(self.method, Unset):
            method = self.method.value

        filter_ = self.filter_

        transportlabel = self.transportlabel

        copy = self.copy

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if channel is not UNSET:
            field_dict["channel"] = channel
        if callback is not UNSET:
            field_dict["callback"] = callback
        if action is not UNSET:
            field_dict["action"] = action
        if method is not UNSET:
            field_dict["method"] = method
        if filter_ is not UNSET:
            field_dict["filter"] = filter_
        if transportlabel is not UNSET:
            field_dict["transportlabel"] = transportlabel
        if copy is not UNSET:
            field_dict["copy"] = copy

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        channel = d.pop("channel", UNSET)

        callback = d.pop("callback", UNSET)

        _action = d.pop("action", UNSET)
        action: ClientAction | Unset
        if isinstance(_action, Unset):
            action = UNSET
        else:
            action = ClientAction(_action)

        _method = d.pop("method", UNSET)
        method: ClientMethod | Unset
        if isinstance(_method, Unset):
            method = UNSET
        else:
            method = ClientMethod(_method)

        filter_ = d.pop("filter", UNSET)

        transportlabel = d.pop("transportlabel", UNSET)

        copy = d.pop("copy", UNSET)

        client = cls(
            id=id,
            channel=channel,
            callback=callback,
            action=action,
            method=method,
            filter_=filter_,
            transportlabel=transportlabel,
            copy=copy,
        )

        client.additional_properties = d
        return client

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
