from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.hazmat import Hazmat
    from ..models.warehouses import Warehouses


T = TypeVar("T", bound="Product")


@_attrs_define
class Product:
    """
    Attributes:
        id (str | Unset): Your internal ID of the product
        package_num (float | Unset):  Example: 1.
        warehouse (str | Unset): Number of the warehouse, as it is added in DeliveryMatch. When the given number does
            not exist, or no number is given, the default is 1. Default: '1'. Example: 2.
        transportlabel (bool | Unset): Returns a pick-transport label for this product Default: False.
        location (str | Unset): Location of the item in the warehouse
        description (str | Unset): Short general description of the contents of the product Example: Electronics.
        content (str | Unset): More detailed description of the content Example: LG Television.
        sku (str | Unset): SKU-number of the product Example: DM123456.
        ean (str | Unset): EAN of the product Example: 123456789.
        hs_code (str | Unset): Harmonized System code Example: 123456.
        dangerous_goods (Hazmat | Unset): General information about the dangerous good
        quantity (int | Unset): Amount of this product in this shipment Example: 5.
        value (float | Unset): Value of the product in the currency format given in shipment Example: 620.
        weight (float | Unset): Weight of the product in kilograms Example: 16.4.
        length (float | Unset): Length of the product in centimeters Example: 130.
        width (float | Unset): Width of the product in centimeters Example: 70.
        height (float | Unset): Height of the product in centimeters Example: 20.
        volume (float | Unset): Volume of the product in m3 Example: 20.
        stock (bool | Unset): Whether product is in stock
        stockdate (str | Unset): Date product is back in stock. Only used if stock is set to false Example: 2022-09-04.
        country_of_origin (str | Unset): Two character code of the country of origin of the product (ISO 3166-1 alpha-2)
            Example: NL.
        item_group (str | Unset): indicate to what itemgroup the item belongs
        amount_per_package (float | Unset): indicate how many shipments are inside the box per item Example: 1.
        warehouses (list[Warehouses] | Unset): List of warehouses
        custom1 (str | Unset): Custom field 1
        custom2 (str | Unset): Custom field 2
        custom3 (str | Unset): Custom field 3
        custom4 (str | Unset): Custom field 4
        custom5 (str | Unset): Custom field 5
        custom6 (str | Unset): Custom field 6
        custom7 (str | Unset): Custom field 7
        custom8 (str | Unset): Custom field 8
        custom9 (str | Unset): Custom field 9
    """

    id: str | Unset = UNSET
    package_num: float | Unset = UNSET
    warehouse: str | Unset = "1"
    transportlabel: bool | Unset = False
    location: str | Unset = UNSET
    description: str | Unset = UNSET
    content: str | Unset = UNSET
    sku: str | Unset = UNSET
    ean: str | Unset = UNSET
    hs_code: str | Unset = UNSET
    dangerous_goods: Hazmat | Unset = UNSET
    quantity: int | Unset = UNSET
    value: float | Unset = UNSET
    weight: float | Unset = UNSET
    length: float | Unset = UNSET
    width: float | Unset = UNSET
    height: float | Unset = UNSET
    volume: float | Unset = UNSET
    stock: bool | Unset = UNSET
    stockdate: str | Unset = UNSET
    country_of_origin: str | Unset = UNSET
    item_group: str | Unset = UNSET
    amount_per_package: float | Unset = UNSET
    warehouses: list[Warehouses] | Unset = UNSET
    custom1: str | Unset = UNSET
    custom2: str | Unset = UNSET
    custom3: str | Unset = UNSET
    custom4: str | Unset = UNSET
    custom5: str | Unset = UNSET
    custom6: str | Unset = UNSET
    custom7: str | Unset = UNSET
    custom8: str | Unset = UNSET
    custom9: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        package_num = self.package_num

        warehouse = self.warehouse

        transportlabel = self.transportlabel

        location = self.location

        description = self.description

        content = self.content

        sku = self.sku

        ean = self.ean

        hs_code = self.hs_code

        dangerous_goods: dict[str, Any] | Unset = UNSET
        if not isinstance(self.dangerous_goods, Unset):
            dangerous_goods = self.dangerous_goods.to_dict()

        quantity = self.quantity

        value = self.value

        weight = self.weight

        length = self.length

        width = self.width

        height = self.height

        volume = self.volume

        stock = self.stock

        stockdate = self.stockdate

        country_of_origin = self.country_of_origin

        item_group = self.item_group

        amount_per_package = self.amount_per_package

        warehouses: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.warehouses, Unset):
            warehouses = []
            for warehouses_item_data in self.warehouses:
                warehouses_item = warehouses_item_data.to_dict()
                warehouses.append(warehouses_item)

        custom1 = self.custom1

        custom2 = self.custom2

        custom3 = self.custom3

        custom4 = self.custom4

        custom5 = self.custom5

        custom6 = self.custom6

        custom7 = self.custom7

        custom8 = self.custom8

        custom9 = self.custom9

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if package_num is not UNSET:
            field_dict["packageNum"] = package_num
        if warehouse is not UNSET:
            field_dict["warehouse"] = warehouse
        if transportlabel is not UNSET:
            field_dict["transportlabel"] = transportlabel
        if location is not UNSET:
            field_dict["location"] = location
        if description is not UNSET:
            field_dict["description"] = description
        if content is not UNSET:
            field_dict["content"] = content
        if sku is not UNSET:
            field_dict["SKU"] = sku
        if ean is not UNSET:
            field_dict["EAN"] = ean
        if hs_code is not UNSET:
            field_dict["hsCode"] = hs_code
        if dangerous_goods is not UNSET:
            field_dict["dangerousGoods"] = dangerous_goods
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if value is not UNSET:
            field_dict["value"] = value
        if weight is not UNSET:
            field_dict["weight"] = weight
        if length is not UNSET:
            field_dict["length"] = length
        if width is not UNSET:
            field_dict["width"] = width
        if height is not UNSET:
            field_dict["height"] = height
        if volume is not UNSET:
            field_dict["volume"] = volume
        if stock is not UNSET:
            field_dict["stock"] = stock
        if stockdate is not UNSET:
            field_dict["stockdate"] = stockdate
        if country_of_origin is not UNSET:
            field_dict["countryOfOrigin"] = country_of_origin
        if item_group is not UNSET:
            field_dict["itemGroup"] = item_group
        if amount_per_package is not UNSET:
            field_dict["amountPerPackage"] = amount_per_package
        if warehouses is not UNSET:
            field_dict["warehouses"] = warehouses
        if custom1 is not UNSET:
            field_dict["custom1"] = custom1
        if custom2 is not UNSET:
            field_dict["custom2"] = custom2
        if custom3 is not UNSET:
            field_dict["custom3"] = custom3
        if custom4 is not UNSET:
            field_dict["custom4"] = custom4
        if custom5 is not UNSET:
            field_dict["custom5"] = custom5
        if custom6 is not UNSET:
            field_dict["custom6"] = custom6
        if custom7 is not UNSET:
            field_dict["custom7"] = custom7
        if custom8 is not UNSET:
            field_dict["custom8"] = custom8
        if custom9 is not UNSET:
            field_dict["custom9"] = custom9

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.hazmat import Hazmat
        from ..models.warehouses import Warehouses

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        package_num = d.pop("packageNum", UNSET)

        warehouse = d.pop("warehouse", UNSET)

        transportlabel = d.pop("transportlabel", UNSET)

        location = d.pop("location", UNSET)

        description = d.pop("description", UNSET)

        content = d.pop("content", UNSET)

        sku = d.pop("SKU", UNSET)

        ean = d.pop("EAN", UNSET)

        hs_code = d.pop("hsCode", UNSET)

        _dangerous_goods = d.pop("dangerousGoods", UNSET)
        dangerous_goods: Hazmat | Unset
        if isinstance(_dangerous_goods, Unset):
            dangerous_goods = UNSET
        else:
            dangerous_goods = Hazmat.from_dict(_dangerous_goods)

        quantity = d.pop("quantity", UNSET)

        value = d.pop("value", UNSET)

        weight = d.pop("weight", UNSET)

        length = d.pop("length", UNSET)

        width = d.pop("width", UNSET)

        height = d.pop("height", UNSET)

        volume = d.pop("volume", UNSET)

        stock = d.pop("stock", UNSET)

        stockdate = d.pop("stockdate", UNSET)

        country_of_origin = d.pop("countryOfOrigin", UNSET)

        item_group = d.pop("itemGroup", UNSET)

        amount_per_package = d.pop("amountPerPackage", UNSET)

        _warehouses = d.pop("warehouses", UNSET)
        warehouses: list[Warehouses] | Unset = UNSET
        if _warehouses is not UNSET:
            warehouses = []
            for warehouses_item_data in _warehouses:
                warehouses_item = Warehouses.from_dict(warehouses_item_data)

                warehouses.append(warehouses_item)

        custom1 = d.pop("custom1", UNSET)

        custom2 = d.pop("custom2", UNSET)

        custom3 = d.pop("custom3", UNSET)

        custom4 = d.pop("custom4", UNSET)

        custom5 = d.pop("custom5", UNSET)

        custom6 = d.pop("custom6", UNSET)

        custom7 = d.pop("custom7", UNSET)

        custom8 = d.pop("custom8", UNSET)

        custom9 = d.pop("custom9", UNSET)

        product = cls(
            id=id,
            package_num=package_num,
            warehouse=warehouse,
            transportlabel=transportlabel,
            location=location,
            description=description,
            content=content,
            sku=sku,
            ean=ean,
            hs_code=hs_code,
            dangerous_goods=dangerous_goods,
            quantity=quantity,
            value=value,
            weight=weight,
            length=length,
            width=width,
            height=height,
            volume=volume,
            stock=stock,
            stockdate=stockdate,
            country_of_origin=country_of_origin,
            item_group=item_group,
            amount_per_package=amount_per_package,
            warehouses=warehouses,
            custom1=custom1,
            custom2=custom2,
            custom3=custom3,
            custom4=custom4,
            custom5=custom5,
            custom6=custom6,
            custom7=custom7,
            custom8=custom8,
            custom9=custom9,
        )

        product.additional_properties = d
        return product

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
