from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.client import Client
    from ..models.customer import Customer
    from ..models.sender import Sender
    from ..models.update_shipment_body_packages import UpdateShipmentBodyPackages
    from ..models.update_shipment_body_quote import UpdateShipmentBodyQuote
    from ..models.update_shipment_body_shipment import UpdateShipmentBodyShipment


T = TypeVar("T", bound="UpdateShipmentBody")


@_attrs_define
class UpdateShipmentBody:
    """
    Attributes:
        client (Client): General information about the client and selected options
        shipment (UpdateShipmentBodyShipment):
        sender (Sender | Unset): Sender address and contact information
        customer (Customer | Unset): Customer address, billing, contact and customs information
        packages (UpdateShipmentBodyPackages | Unset): When given, DeliveryMatch does not use quote information to
            generate packages
        quote (UpdateShipmentBodyQuote | Unset): Information about the items in the shipment
        fragile_goods (bool | Unset): When the shipment contains fragile goods, this field has to be set to true
            Default: False.
        dangerous_goods (bool | Unset): When the shipment contains dangerous goods, this fields has to be set to true
            Default: False.
        price_incl (float | Unset): Total value of the shipment including VAT
        price_excl (float | Unset): Total value of the shipment excluding VAT
        weight (float | Unset): Total weight of the shipment in kilograms
        price_currency (str | Unset): Currency of the item value Example: EUR.
    """

    client: Client
    shipment: UpdateShipmentBodyShipment
    sender: Sender | Unset = UNSET
    customer: Customer | Unset = UNSET
    packages: UpdateShipmentBodyPackages | Unset = UNSET
    quote: UpdateShipmentBodyQuote | Unset = UNSET
    fragile_goods: bool | Unset = False
    dangerous_goods: bool | Unset = False
    price_incl: float | Unset = UNSET
    price_excl: float | Unset = UNSET
    weight: float | Unset = UNSET
    price_currency: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        client = self.client.to_dict()

        shipment = self.shipment.to_dict()

        sender: dict[str, Any] | Unset = UNSET
        if not isinstance(self.sender, Unset):
            sender = self.sender.to_dict()

        customer: dict[str, Any] | Unset = UNSET
        if not isinstance(self.customer, Unset):
            customer = self.customer.to_dict()

        packages: dict[str, Any] | Unset = UNSET
        if not isinstance(self.packages, Unset):
            packages = self.packages.to_dict()

        quote: dict[str, Any] | Unset = UNSET
        if not isinstance(self.quote, Unset):
            quote = self.quote.to_dict()

        fragile_goods = self.fragile_goods

        dangerous_goods = self.dangerous_goods

        price_incl = self.price_incl

        price_excl = self.price_excl

        weight = self.weight

        price_currency = self.price_currency

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "client": client,
                "shipment": shipment,
            }
        )
        if sender is not UNSET:
            field_dict["sender"] = sender
        if customer is not UNSET:
            field_dict["customer"] = customer
        if packages is not UNSET:
            field_dict["packages"] = packages
        if quote is not UNSET:
            field_dict["quote"] = quote
        if fragile_goods is not UNSET:
            field_dict["fragileGoods"] = fragile_goods
        if dangerous_goods is not UNSET:
            field_dict["dangerousGoods"] = dangerous_goods
        if price_incl is not UNSET:
            field_dict["priceIncl"] = price_incl
        if price_excl is not UNSET:
            field_dict["priceExcl"] = price_excl
        if weight is not UNSET:
            field_dict["weight"] = weight
        if price_currency is not UNSET:
            field_dict["priceCurrency"] = price_currency

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.client import Client
        from ..models.customer import Customer
        from ..models.sender import Sender
        from ..models.update_shipment_body_packages import UpdateShipmentBodyPackages
        from ..models.update_shipment_body_quote import UpdateShipmentBodyQuote
        from ..models.update_shipment_body_shipment import UpdateShipmentBodyShipment

        d = dict(src_dict)
        client = Client.from_dict(d.pop("client"))

        shipment = UpdateShipmentBodyShipment.from_dict(d.pop("shipment"))

        _sender = d.pop("sender", UNSET)
        sender: Sender | Unset
        if isinstance(_sender, Unset):
            sender = UNSET
        else:
            sender = Sender.from_dict(_sender)

        _customer = d.pop("customer", UNSET)
        customer: Customer | Unset
        if isinstance(_customer, Unset):
            customer = UNSET
        else:
            customer = Customer.from_dict(_customer)

        _packages = d.pop("packages", UNSET)
        packages: UpdateShipmentBodyPackages | Unset
        if isinstance(_packages, Unset):
            packages = UNSET
        else:
            packages = UpdateShipmentBodyPackages.from_dict(_packages)

        _quote = d.pop("quote", UNSET)
        quote: UpdateShipmentBodyQuote | Unset
        if isinstance(_quote, Unset):
            quote = UNSET
        else:
            quote = UpdateShipmentBodyQuote.from_dict(_quote)

        fragile_goods = d.pop("fragileGoods", UNSET)

        dangerous_goods = d.pop("dangerousGoods", UNSET)

        price_incl = d.pop("priceIncl", UNSET)

        price_excl = d.pop("priceExcl", UNSET)

        weight = d.pop("weight", UNSET)

        price_currency = d.pop("priceCurrency", UNSET)

        update_shipment_body = cls(
            client=client,
            shipment=shipment,
            sender=sender,
            customer=customer,
            packages=packages,
            quote=quote,
            fragile_goods=fragile_goods,
            dangerous_goods=dangerous_goods,
            price_incl=price_incl,
            price_excl=price_excl,
            weight=weight,
            price_currency=price_currency,
        )

        update_shipment_body.additional_properties = d
        return update_shipment_body

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
