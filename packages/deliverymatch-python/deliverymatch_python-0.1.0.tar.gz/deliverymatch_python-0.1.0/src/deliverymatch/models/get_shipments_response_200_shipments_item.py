from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.status import Status
from ..types import UNSET, Unset

T = TypeVar("T", bound="GetShipmentsResponse200ShipmentsItem")


@_attrs_define
class GetShipmentsResponse200ShipmentsItem:
    """
    Attributes:
        id (float | Unset):
        order_number (str | Unset):
        reference (str | Unset):
        sender_name (str | Unset):
        receiver_name (str | Unset):
        zipcode (str | Unset):
        date_added (str | Unset):
        channel (str | Unset):
        country (str | Unset):
        status (Status | Unset): Shipment status
        carrier_name (str | Unset):
        service_level (str | Unset):
        barcodes (str | Unset):
        zpl (str | Unset):
        weight (float | Unset):
        email (str | Unset):
        street (str | Unset):
        houseno (int | Unset):
        housenoext (str | Unset):
        city (str | Unset):
        company_name (bool | Unset):
        sellprice (float | Unset):
        buyprice (float | Unset):
        address1 (str | Unset):
        address2 (str | Unset):
        note (str | Unset):
        phonenumber (str | Unset):
    """

    id: float | Unset = UNSET
    order_number: str | Unset = UNSET
    reference: str | Unset = UNSET
    sender_name: str | Unset = UNSET
    receiver_name: str | Unset = UNSET
    zipcode: str | Unset = UNSET
    date_added: str | Unset = UNSET
    channel: str | Unset = UNSET
    country: str | Unset = UNSET
    status: Status | Unset = UNSET
    carrier_name: str | Unset = UNSET
    service_level: str | Unset = UNSET
    barcodes: str | Unset = UNSET
    zpl: str | Unset = UNSET
    weight: float | Unset = UNSET
    email: str | Unset = UNSET
    street: str | Unset = UNSET
    houseno: int | Unset = UNSET
    housenoext: str | Unset = UNSET
    city: str | Unset = UNSET
    company_name: bool | Unset = UNSET
    sellprice: float | Unset = UNSET
    buyprice: float | Unset = UNSET
    address1: str | Unset = UNSET
    address2: str | Unset = UNSET
    note: str | Unset = UNSET
    phonenumber: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        order_number = self.order_number

        reference = self.reference

        sender_name = self.sender_name

        receiver_name = self.receiver_name

        zipcode = self.zipcode

        date_added = self.date_added

        channel = self.channel

        country = self.country

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        carrier_name = self.carrier_name

        service_level = self.service_level

        barcodes = self.barcodes

        zpl = self.zpl

        weight = self.weight

        email = self.email

        street = self.street

        houseno = self.houseno

        housenoext = self.housenoext

        city = self.city

        company_name = self.company_name

        sellprice = self.sellprice

        buyprice = self.buyprice

        address1 = self.address1

        address2 = self.address2

        note = self.note

        phonenumber = self.phonenumber

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if order_number is not UNSET:
            field_dict["orderNumber"] = order_number
        if reference is not UNSET:
            field_dict["reference"] = reference
        if sender_name is not UNSET:
            field_dict["senderName"] = sender_name
        if receiver_name is not UNSET:
            field_dict["receiverName"] = receiver_name
        if zipcode is not UNSET:
            field_dict["zipcode"] = zipcode
        if date_added is not UNSET:
            field_dict["dateAdded"] = date_added
        if channel is not UNSET:
            field_dict["channel"] = channel
        if country is not UNSET:
            field_dict["country"] = country
        if status is not UNSET:
            field_dict["status"] = status
        if carrier_name is not UNSET:
            field_dict["carrierName"] = carrier_name
        if service_level is not UNSET:
            field_dict["serviceLevel"] = service_level
        if barcodes is not UNSET:
            field_dict["barcodes"] = barcodes
        if zpl is not UNSET:
            field_dict["zpl"] = zpl
        if weight is not UNSET:
            field_dict["weight"] = weight
        if email is not UNSET:
            field_dict["email"] = email
        if street is not UNSET:
            field_dict["street"] = street
        if houseno is not UNSET:
            field_dict["houseno"] = houseno
        if housenoext is not UNSET:
            field_dict["housenoext"] = housenoext
        if city is not UNSET:
            field_dict["city"] = city
        if company_name is not UNSET:
            field_dict["companyName"] = company_name
        if sellprice is not UNSET:
            field_dict["sellprice"] = sellprice
        if buyprice is not UNSET:
            field_dict["buyprice"] = buyprice
        if address1 is not UNSET:
            field_dict["address1"] = address1
        if address2 is not UNSET:
            field_dict["address2"] = address2
        if note is not UNSET:
            field_dict["note"] = note
        if phonenumber is not UNSET:
            field_dict["phonenumber"] = phonenumber

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        order_number = d.pop("orderNumber", UNSET)

        reference = d.pop("reference", UNSET)

        sender_name = d.pop("senderName", UNSET)

        receiver_name = d.pop("receiverName", UNSET)

        zipcode = d.pop("zipcode", UNSET)

        date_added = d.pop("dateAdded", UNSET)

        channel = d.pop("channel", UNSET)

        country = d.pop("country", UNSET)

        _status = d.pop("status", UNSET)
        status: Status | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = Status(_status)

        carrier_name = d.pop("carrierName", UNSET)

        service_level = d.pop("serviceLevel", UNSET)

        barcodes = d.pop("barcodes", UNSET)

        zpl = d.pop("zpl", UNSET)

        weight = d.pop("weight", UNSET)

        email = d.pop("email", UNSET)

        street = d.pop("street", UNSET)

        houseno = d.pop("houseno", UNSET)

        housenoext = d.pop("housenoext", UNSET)

        city = d.pop("city", UNSET)

        company_name = d.pop("companyName", UNSET)

        sellprice = d.pop("sellprice", UNSET)

        buyprice = d.pop("buyprice", UNSET)

        address1 = d.pop("address1", UNSET)

        address2 = d.pop("address2", UNSET)

        note = d.pop("note", UNSET)

        phonenumber = d.pop("phonenumber", UNSET)

        get_shipments_response_200_shipments_item = cls(
            id=id,
            order_number=order_number,
            reference=reference,
            sender_name=sender_name,
            receiver_name=receiver_name,
            zipcode=zipcode,
            date_added=date_added,
            channel=channel,
            country=country,
            status=status,
            carrier_name=carrier_name,
            service_level=service_level,
            barcodes=barcodes,
            zpl=zpl,
            weight=weight,
            email=email,
            street=street,
            houseno=houseno,
            housenoext=housenoext,
            city=city,
            company_name=company_name,
            sellprice=sellprice,
            buyprice=buyprice,
            address1=address1,
            address2=address2,
            note=note,
            phonenumber=phonenumber,
        )

        get_shipments_response_200_shipments_item.additional_properties = d
        return get_shipments_response_200_shipments_item

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
