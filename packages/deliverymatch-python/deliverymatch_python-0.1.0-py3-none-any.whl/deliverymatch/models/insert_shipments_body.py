from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.client import Client
    from ..models.customer import Customer
    from ..models.insert_shipments_body_packages import InsertShipmentsBodyPackages
    from ..models.insert_shipments_body_quote import InsertShipmentsBodyQuote
    from ..models.sender import Sender
    from ..models.shipment import Shipment


T = TypeVar("T", bound="InsertShipmentsBody")


@_attrs_define
class InsertShipmentsBody:
    """
    Attributes:
        client (Client): General information about the client and selected options
        shipment (Shipment): General information about the shipment
        customer (Customer): Customer address, billing, contact and customs information
        quote (InsertShipmentsBodyQuote): Information about the items in the shipment
        price_incl (float): Total value of the shipment including VAT
        weight (float): Total weight of the shipment in kilograms
        sender (Sender | Unset): Sender address and contact information
        packages (InsertShipmentsBodyPackages | Unset): When given, DeliveryMatch does not use quote information to
            generate packages
        fragile_goods (bool | Unset): When the shipment contains fragile goods, this field has to be set to true
            Default: False.
        dangerous_goods (bool | Unset): When the shipment contains dangerous goods, this fields has to be set to true
            Default: False.
        price_excl (float | Unset): Total value of the shipment excluding VAT
        price_currency (str | Unset): Currency of the item value Example: EUR.
    """

    client: Client
    shipment: Shipment
    customer: Customer
    quote: InsertShipmentsBodyQuote
    price_incl: float
    weight: float
    sender: Sender | Unset = UNSET
    packages: InsertShipmentsBodyPackages | Unset = UNSET
    fragile_goods: bool | Unset = False
    dangerous_goods: bool | Unset = False
    price_excl: float | Unset = UNSET
    price_currency: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        client = self.client.to_dict()

        shipment = self.shipment.to_dict()

        customer = self.customer.to_dict()

        quote = self.quote.to_dict()

        price_incl = self.price_incl

        weight = self.weight

        sender: dict[str, Any] | Unset = UNSET
        if not isinstance(self.sender, Unset):
            sender = self.sender.to_dict()

        packages: dict[str, Any] | Unset = UNSET
        if not isinstance(self.packages, Unset):
            packages = self.packages.to_dict()

        fragile_goods = self.fragile_goods

        dangerous_goods = self.dangerous_goods

        price_excl = self.price_excl

        price_currency = self.price_currency

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "client": client,
                "shipment": shipment,
                "customer": customer,
                "quote": quote,
                "priceIncl": price_incl,
                "weight": weight,
            }
        )
        if sender is not UNSET:
            field_dict["sender"] = sender
        if packages is not UNSET:
            field_dict["packages"] = packages
        if fragile_goods is not UNSET:
            field_dict["fragileGoods"] = fragile_goods
        if dangerous_goods is not UNSET:
            field_dict["dangerousGoods"] = dangerous_goods
        if price_excl is not UNSET:
            field_dict["priceExcl"] = price_excl
        if price_currency is not UNSET:
            field_dict["priceCurrency"] = price_currency

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.client import Client
        from ..models.customer import Customer
        from ..models.insert_shipments_body_packages import InsertShipmentsBodyPackages
        from ..models.insert_shipments_body_quote import InsertShipmentsBodyQuote
        from ..models.sender import Sender
        from ..models.shipment import Shipment

        d = dict(src_dict)
        client = Client.from_dict(d.pop("client"))

        shipment = Shipment.from_dict(d.pop("shipment"))

        customer = Customer.from_dict(d.pop("customer"))

        quote = InsertShipmentsBodyQuote.from_dict(d.pop("quote"))

        price_incl = d.pop("priceIncl")

        weight = d.pop("weight")

        _sender = d.pop("sender", UNSET)
        sender: Sender | Unset
        if isinstance(_sender, Unset):
            sender = UNSET
        else:
            sender = Sender.from_dict(_sender)

        _packages = d.pop("packages", UNSET)
        packages: InsertShipmentsBodyPackages | Unset
        if isinstance(_packages, Unset):
            packages = UNSET
        else:
            packages = InsertShipmentsBodyPackages.from_dict(_packages)

        fragile_goods = d.pop("fragileGoods", UNSET)

        dangerous_goods = d.pop("dangerousGoods", UNSET)

        price_excl = d.pop("priceExcl", UNSET)

        price_currency = d.pop("priceCurrency", UNSET)

        insert_shipments_body = cls(
            client=client,
            shipment=shipment,
            customer=customer,
            quote=quote,
            price_incl=price_incl,
            weight=weight,
            sender=sender,
            packages=packages,
            fragile_goods=fragile_goods,
            dangerous_goods=dangerous_goods,
            price_excl=price_excl,
            price_currency=price_currency,
        )

        insert_shipments_body.additional_properties = d
        return insert_shipments_body

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
