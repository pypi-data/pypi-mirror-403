from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_shipment_response_200_carrier import GetShipmentResponse200Carrier
    from ..models.get_shipment_response_200_client import GetShipmentResponse200Client
    from ..models.get_shipment_response_200_customer import GetShipmentResponse200Customer
    from ..models.get_shipment_response_200_packages import GetShipmentResponse200Packages
    from ..models.get_shipment_response_200_quote import GetShipmentResponse200Quote
    from ..models.get_shipment_response_200_sender import GetShipmentResponse200Sender
    from ..models.get_shipment_response_200_service_level import GetShipmentResponse200ServiceLevel
    from ..models.get_shipment_response_200_shipment import GetShipmentResponse200Shipment
    from ..models.get_shipment_response_200_shipment_method import GetShipmentResponse200ShipmentMethod


T = TypeVar("T", bound="GetShipmentResponse200")


@_attrs_define
class GetShipmentResponse200:
    """
    Attributes:
        client (GetShipmentResponse200Client | Unset):
        shipment (GetShipmentResponse200Shipment | Unset):
        shipment_method (GetShipmentResponse200ShipmentMethod | Unset):
        customer (GetShipmentResponse200Customer | Unset):
        sender (GetShipmentResponse200Sender | Unset):
        carrier (GetShipmentResponse200Carrier | Unset):
        service_level (GetShipmentResponse200ServiceLevel | Unset):
        barcodes (list[str] | Unset):
        packages (GetShipmentResponse200Packages | Unset):
        quote (GetShipmentResponse200Quote | Unset):
        fragile_goods (bool | Unset):
        dangerous_goods (bool | Unset):
        price_incl (float | Unset):
        weight (float | Unset):
        colli (float | Unset):
    """

    client: GetShipmentResponse200Client | Unset = UNSET
    shipment: GetShipmentResponse200Shipment | Unset = UNSET
    shipment_method: GetShipmentResponse200ShipmentMethod | Unset = UNSET
    customer: GetShipmentResponse200Customer | Unset = UNSET
    sender: GetShipmentResponse200Sender | Unset = UNSET
    carrier: GetShipmentResponse200Carrier | Unset = UNSET
    service_level: GetShipmentResponse200ServiceLevel | Unset = UNSET
    barcodes: list[str] | Unset = UNSET
    packages: GetShipmentResponse200Packages | Unset = UNSET
    quote: GetShipmentResponse200Quote | Unset = UNSET
    fragile_goods: bool | Unset = UNSET
    dangerous_goods: bool | Unset = UNSET
    price_incl: float | Unset = UNSET
    weight: float | Unset = UNSET
    colli: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        client: dict[str, Any] | Unset = UNSET
        if not isinstance(self.client, Unset):
            client = self.client.to_dict()

        shipment: dict[str, Any] | Unset = UNSET
        if not isinstance(self.shipment, Unset):
            shipment = self.shipment.to_dict()

        shipment_method: dict[str, Any] | Unset = UNSET
        if not isinstance(self.shipment_method, Unset):
            shipment_method = self.shipment_method.to_dict()

        customer: dict[str, Any] | Unset = UNSET
        if not isinstance(self.customer, Unset):
            customer = self.customer.to_dict()

        sender: dict[str, Any] | Unset = UNSET
        if not isinstance(self.sender, Unset):
            sender = self.sender.to_dict()

        carrier: dict[str, Any] | Unset = UNSET
        if not isinstance(self.carrier, Unset):
            carrier = self.carrier.to_dict()

        service_level: dict[str, Any] | Unset = UNSET
        if not isinstance(self.service_level, Unset):
            service_level = self.service_level.to_dict()

        barcodes: list[str] | Unset = UNSET
        if not isinstance(self.barcodes, Unset):
            barcodes = self.barcodes

        packages: dict[str, Any] | Unset = UNSET
        if not isinstance(self.packages, Unset):
            packages = self.packages.to_dict()

        quote: dict[str, Any] | Unset = UNSET
        if not isinstance(self.quote, Unset):
            quote = self.quote.to_dict()

        fragile_goods = self.fragile_goods

        dangerous_goods = self.dangerous_goods

        price_incl = self.price_incl

        weight = self.weight

        colli = self.colli

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if client is not UNSET:
            field_dict["client"] = client
        if shipment is not UNSET:
            field_dict["shipment"] = shipment
        if shipment_method is not UNSET:
            field_dict["shipmentMethod"] = shipment_method
        if customer is not UNSET:
            field_dict["customer"] = customer
        if sender is not UNSET:
            field_dict["sender"] = sender
        if carrier is not UNSET:
            field_dict["carrier"] = carrier
        if service_level is not UNSET:
            field_dict["serviceLevel"] = service_level
        if barcodes is not UNSET:
            field_dict["barcodes"] = barcodes
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
        if weight is not UNSET:
            field_dict["weight"] = weight
        if colli is not UNSET:
            field_dict["colli"] = colli

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_shipment_response_200_carrier import GetShipmentResponse200Carrier
        from ..models.get_shipment_response_200_client import GetShipmentResponse200Client
        from ..models.get_shipment_response_200_customer import GetShipmentResponse200Customer
        from ..models.get_shipment_response_200_packages import GetShipmentResponse200Packages
        from ..models.get_shipment_response_200_quote import GetShipmentResponse200Quote
        from ..models.get_shipment_response_200_sender import GetShipmentResponse200Sender
        from ..models.get_shipment_response_200_service_level import GetShipmentResponse200ServiceLevel
        from ..models.get_shipment_response_200_shipment import GetShipmentResponse200Shipment
        from ..models.get_shipment_response_200_shipment_method import GetShipmentResponse200ShipmentMethod

        d = dict(src_dict)
        _client = d.pop("client", UNSET)
        client: GetShipmentResponse200Client | Unset
        if isinstance(_client, Unset):
            client = UNSET
        else:
            client = GetShipmentResponse200Client.from_dict(_client)

        _shipment = d.pop("shipment", UNSET)
        shipment: GetShipmentResponse200Shipment | Unset
        if isinstance(_shipment, Unset):
            shipment = UNSET
        else:
            shipment = GetShipmentResponse200Shipment.from_dict(_shipment)

        _shipment_method = d.pop("shipmentMethod", UNSET)
        shipment_method: GetShipmentResponse200ShipmentMethod | Unset
        if isinstance(_shipment_method, Unset):
            shipment_method = UNSET
        else:
            shipment_method = GetShipmentResponse200ShipmentMethod.from_dict(_shipment_method)

        _customer = d.pop("customer", UNSET)
        customer: GetShipmentResponse200Customer | Unset
        if isinstance(_customer, Unset):
            customer = UNSET
        else:
            customer = GetShipmentResponse200Customer.from_dict(_customer)

        _sender = d.pop("sender", UNSET)
        sender: GetShipmentResponse200Sender | Unset
        if isinstance(_sender, Unset):
            sender = UNSET
        else:
            sender = GetShipmentResponse200Sender.from_dict(_sender)

        _carrier = d.pop("carrier", UNSET)
        carrier: GetShipmentResponse200Carrier | Unset
        if isinstance(_carrier, Unset):
            carrier = UNSET
        else:
            carrier = GetShipmentResponse200Carrier.from_dict(_carrier)

        _service_level = d.pop("serviceLevel", UNSET)
        service_level: GetShipmentResponse200ServiceLevel | Unset
        if isinstance(_service_level, Unset):
            service_level = UNSET
        else:
            service_level = GetShipmentResponse200ServiceLevel.from_dict(_service_level)

        barcodes = cast(list[str], d.pop("barcodes", UNSET))

        _packages = d.pop("packages", UNSET)
        packages: GetShipmentResponse200Packages | Unset
        if isinstance(_packages, Unset):
            packages = UNSET
        else:
            packages = GetShipmentResponse200Packages.from_dict(_packages)

        _quote = d.pop("quote", UNSET)
        quote: GetShipmentResponse200Quote | Unset
        if isinstance(_quote, Unset):
            quote = UNSET
        else:
            quote = GetShipmentResponse200Quote.from_dict(_quote)

        fragile_goods = d.pop("fragileGoods", UNSET)

        dangerous_goods = d.pop("dangerousGoods", UNSET)

        price_incl = d.pop("priceIncl", UNSET)

        weight = d.pop("weight", UNSET)

        colli = d.pop("colli", UNSET)

        get_shipment_response_200 = cls(
            client=client,
            shipment=shipment,
            shipment_method=shipment_method,
            customer=customer,
            sender=sender,
            carrier=carrier,
            service_level=service_level,
            barcodes=barcodes,
            packages=packages,
            quote=quote,
            fragile_goods=fragile_goods,
            dangerous_goods=dangerous_goods,
            price_incl=price_incl,
            weight=weight,
            colli=colli,
        )

        get_shipment_response_200.additional_properties = d
        return get_shipment_response_200

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
