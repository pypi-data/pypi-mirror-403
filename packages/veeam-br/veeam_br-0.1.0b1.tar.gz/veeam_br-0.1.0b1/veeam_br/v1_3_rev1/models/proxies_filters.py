from collections.abc import Mapping
from typing import Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_proxies_filters_order_column import EProxiesFiltersOrderColumn
from ..models.e_proxy_type import EProxyType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProxiesFilters")


@_attrs_define
class ProxiesFilters:
    """
    Attributes:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):
        order_column (Union[Unset, EProxiesFiltersOrderColumn]):
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        type_filter (Union[Unset, list[EProxyType]]):
        host_id_filter (Union[Unset, UUID]):
    """

    skip: Union[Unset, int] = UNSET
    limit: Union[Unset, int] = UNSET
    order_column: Union[Unset, EProxiesFiltersOrderColumn] = UNSET
    order_asc: Union[Unset, bool] = UNSET
    name_filter: Union[Unset, str] = UNSET
    type_filter: Union[Unset, list[EProxyType]] = UNSET
    host_id_filter: Union[Unset, UUID] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: Union[Unset, str] = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        name_filter = self.name_filter

        type_filter: Union[Unset, list[str]] = UNSET
        if not isinstance(self.type_filter, Unset):
            type_filter = []
            for type_filter_item_data in self.type_filter:
                type_filter_item = type_filter_item_data.value
                type_filter.append(type_filter_item)

        host_id_filter: Union[Unset, str] = UNSET
        if not isinstance(self.host_id_filter, Unset):
            host_id_filter = str(self.host_id_filter)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if skip is not UNSET:
            field_dict["skip"] = skip
        if limit is not UNSET:
            field_dict["limit"] = limit
        if order_column is not UNSET:
            field_dict["orderColumn"] = order_column
        if order_asc is not UNSET:
            field_dict["orderAsc"] = order_asc
        if name_filter is not UNSET:
            field_dict["nameFilter"] = name_filter
        if type_filter is not UNSET:
            field_dict["typeFilter"] = type_filter
        if host_id_filter is not UNSET:
            field_dict["hostIdFilter"] = host_id_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: Union[Unset, EProxiesFiltersOrderColumn]
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = EProxiesFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        name_filter = d.pop("nameFilter", UNSET)

        type_filter = []
        _type_filter = d.pop("typeFilter", UNSET)
        for type_filter_item_data in _type_filter or []:
            type_filter_item = EProxyType(type_filter_item_data)

            type_filter.append(type_filter_item)

        _host_id_filter = d.pop("hostIdFilter", UNSET)
        host_id_filter: Union[Unset, UUID]
        if isinstance(_host_id_filter, Unset):
            host_id_filter = UNSET
        else:
            host_id_filter = UUID(_host_id_filter)

        proxies_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            type_filter=type_filter,
            host_id_filter=host_id_filter,
        )

        proxies_filters.additional_properties = d
        return proxies_filters

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
