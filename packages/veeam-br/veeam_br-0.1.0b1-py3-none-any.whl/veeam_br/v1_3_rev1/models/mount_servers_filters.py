from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_mount_server_type import EMountServerType
from ..models.e_mount_servers_filters_order_column import EMountServersFiltersOrderColumn
from ..types import UNSET, Unset

T = TypeVar("T", bound="MountServersFilters")


@_attrs_define
class MountServersFilters:
    """Mount server filters. Using the filters reduces not only the number of records in the response body but also the
    response time.

        Attributes:
            skip (Union[Unset, int]): Number of mount servers to skip.
            limit (Union[Unset, int]): Maximum number of mount servers to return.
            order_column (Union[Unset, EMountServersFiltersOrderColumn]): Sorts mount servers by one of the mount server
                parameters.
            order_asc (Union[Unset, bool]): If `true`, sorts mount servers in ascending order by the `orderColumn`
                parameter.
            write_cache_folder_filter (Union[Unset, str]): Filters mount servers by the `writeCacheFolder` pattern. The
                pattern can match any repository parameter. To substitute one or more characters, use the asterisk (*) character
                at the beginning, at the end or both.
            type_filter (Union[Unset, EMountServerType]): Mount server type.
            is_default_filter (Union[Unset, bool]): If `true`, shows only mount servers that are set as default.
    """

    skip: Union[Unset, int] = UNSET
    limit: Union[Unset, int] = UNSET
    order_column: Union[Unset, EMountServersFiltersOrderColumn] = UNSET
    order_asc: Union[Unset, bool] = UNSET
    write_cache_folder_filter: Union[Unset, str] = UNSET
    type_filter: Union[Unset, EMountServerType] = UNSET
    is_default_filter: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: Union[Unset, str] = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        write_cache_folder_filter = self.write_cache_folder_filter

        type_filter: Union[Unset, str] = UNSET
        if not isinstance(self.type_filter, Unset):
            type_filter = self.type_filter.value

        is_default_filter = self.is_default_filter

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
        if write_cache_folder_filter is not UNSET:
            field_dict["writeCacheFolderFilter"] = write_cache_folder_filter
        if type_filter is not UNSET:
            field_dict["typeFilter"] = type_filter
        if is_default_filter is not UNSET:
            field_dict["isDefaultFilter"] = is_default_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: Union[Unset, EMountServersFiltersOrderColumn]
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = EMountServersFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        write_cache_folder_filter = d.pop("writeCacheFolderFilter", UNSET)

        _type_filter = d.pop("typeFilter", UNSET)
        type_filter: Union[Unset, EMountServerType]
        if isinstance(_type_filter, Unset):
            type_filter = UNSET
        else:
            type_filter = EMountServerType(_type_filter)

        is_default_filter = d.pop("isDefaultFilter", UNSET)

        mount_servers_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            write_cache_folder_filter=write_cache_folder_filter,
            type_filter=type_filter,
            is_default_filter=is_default_filter,
        )

        mount_servers_filters.additional_properties = d
        return mount_servers_filters

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
