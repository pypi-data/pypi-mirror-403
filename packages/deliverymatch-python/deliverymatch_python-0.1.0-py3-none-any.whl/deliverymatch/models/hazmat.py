from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.hazmat_mass_unit import HazmatMassUnit
from ..types import UNSET, Unset

T = TypeVar("T", bound="Hazmat")


@_attrs_define
class Hazmat:
    """General information about the dangerous good

    Attributes:
        technical_name (str | Unset): Technical name of the product
        shipping_name (str | Unset): Shipping name of the product
        main_danger (str | Unset): The main danger of the product
        class_ (str | Unset): Class of the product
        subclass (str | Unset): Subclass of the product
        packing_group (int | Unset): Packing group 1 (greatest danger), 2 (medium danger) or 3 (least danger)
        un (int | Unset): Four digit UN number Example: 3481.
        unp (str | Unset): Extended UN number Example: 3481.
        gross_mass (float | Unset): Gross mass of the dangerous good and packaging. Can be in grams, kg or liter
        net_mass (float | Unset): Net mass of the dangerous good. Can be in grams, kg or liter
        mass_unit (HazmatMassUnit | Unset): Unit of the amount provided in the previous two fields
        lq (bool | Unset): Limited quantity
        nos (str | Unset): Not otherwise specified
        environment_hazard (bool | Unset): Hazardous for environment
        tunnel_code (str | Unset):
        classification_code (str | Unset):
        packing_type (str | Unset):
        properties (str | Unset):
        labels (str | Unset):
        transport_category (int | Unset): Category of transport
        packing_instructions (str | Unset):
    """

    technical_name: str | Unset = UNSET
    shipping_name: str | Unset = UNSET
    main_danger: str | Unset = UNSET
    class_: str | Unset = UNSET
    subclass: str | Unset = UNSET
    packing_group: int | Unset = UNSET
    un: int | Unset = UNSET
    unp: str | Unset = UNSET
    gross_mass: float | Unset = UNSET
    net_mass: float | Unset = UNSET
    mass_unit: HazmatMassUnit | Unset = UNSET
    lq: bool | Unset = UNSET
    nos: str | Unset = UNSET
    environment_hazard: bool | Unset = UNSET
    tunnel_code: str | Unset = UNSET
    classification_code: str | Unset = UNSET
    packing_type: str | Unset = UNSET
    properties: str | Unset = UNSET
    labels: str | Unset = UNSET
    transport_category: int | Unset = UNSET
    packing_instructions: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        technical_name = self.technical_name

        shipping_name = self.shipping_name

        main_danger = self.main_danger

        class_ = self.class_

        subclass = self.subclass

        packing_group = self.packing_group

        un = self.un

        unp = self.unp

        gross_mass = self.gross_mass

        net_mass = self.net_mass

        mass_unit: str | Unset = UNSET
        if not isinstance(self.mass_unit, Unset):
            mass_unit = self.mass_unit.value

        lq = self.lq

        nos = self.nos

        environment_hazard = self.environment_hazard

        tunnel_code = self.tunnel_code

        classification_code = self.classification_code

        packing_type = self.packing_type

        properties = self.properties

        labels = self.labels

        transport_category = self.transport_category

        packing_instructions = self.packing_instructions

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if technical_name is not UNSET:
            field_dict["technicalName"] = technical_name
        if shipping_name is not UNSET:
            field_dict["shippingName"] = shipping_name
        if main_danger is not UNSET:
            field_dict["mainDanger"] = main_danger
        if class_ is not UNSET:
            field_dict["class"] = class_
        if subclass is not UNSET:
            field_dict["subclass"] = subclass
        if packing_group is not UNSET:
            field_dict["packingGroup"] = packing_group
        if un is not UNSET:
            field_dict["UN"] = un
        if unp is not UNSET:
            field_dict["UNP"] = unp
        if gross_mass is not UNSET:
            field_dict["grossMass"] = gross_mass
        if net_mass is not UNSET:
            field_dict["netMass"] = net_mass
        if mass_unit is not UNSET:
            field_dict["massUnit"] = mass_unit
        if lq is not UNSET:
            field_dict["LQ"] = lq
        if nos is not UNSET:
            field_dict["NOS"] = nos
        if environment_hazard is not UNSET:
            field_dict["environmentHazard"] = environment_hazard
        if tunnel_code is not UNSET:
            field_dict["tunnelCode"] = tunnel_code
        if classification_code is not UNSET:
            field_dict["classificationCode"] = classification_code
        if packing_type is not UNSET:
            field_dict["packingType"] = packing_type
        if properties is not UNSET:
            field_dict["properties"] = properties
        if labels is not UNSET:
            field_dict["labels"] = labels
        if transport_category is not UNSET:
            field_dict["transportCategory"] = transport_category
        if packing_instructions is not UNSET:
            field_dict["packingInstructions"] = packing_instructions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        technical_name = d.pop("technicalName", UNSET)

        shipping_name = d.pop("shippingName", UNSET)

        main_danger = d.pop("mainDanger", UNSET)

        class_ = d.pop("class", UNSET)

        subclass = d.pop("subclass", UNSET)

        packing_group = d.pop("packingGroup", UNSET)

        un = d.pop("UN", UNSET)

        unp = d.pop("UNP", UNSET)

        gross_mass = d.pop("grossMass", UNSET)

        net_mass = d.pop("netMass", UNSET)

        _mass_unit = d.pop("massUnit", UNSET)
        mass_unit: HazmatMassUnit | Unset
        if isinstance(_mass_unit, Unset):
            mass_unit = UNSET
        else:
            mass_unit = HazmatMassUnit(_mass_unit)

        lq = d.pop("LQ", UNSET)

        nos = d.pop("NOS", UNSET)

        environment_hazard = d.pop("environmentHazard", UNSET)

        tunnel_code = d.pop("tunnelCode", UNSET)

        classification_code = d.pop("classificationCode", UNSET)

        packing_type = d.pop("packingType", UNSET)

        properties = d.pop("properties", UNSET)

        labels = d.pop("labels", UNSET)

        transport_category = d.pop("transportCategory", UNSET)

        packing_instructions = d.pop("packingInstructions", UNSET)

        hazmat = cls(
            technical_name=technical_name,
            shipping_name=shipping_name,
            main_danger=main_danger,
            class_=class_,
            subclass=subclass,
            packing_group=packing_group,
            un=un,
            unp=unp,
            gross_mass=gross_mass,
            net_mass=net_mass,
            mass_unit=mass_unit,
            lq=lq,
            nos=nos,
            environment_hazard=environment_hazard,
            tunnel_code=tunnel_code,
            classification_code=classification_code,
            packing_type=packing_type,
            properties=properties,
            labels=labels,
            transport_category=transport_category,
            packing_instructions=packing_instructions,
        )

        hazmat.additional_properties = d
        return hazmat

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
