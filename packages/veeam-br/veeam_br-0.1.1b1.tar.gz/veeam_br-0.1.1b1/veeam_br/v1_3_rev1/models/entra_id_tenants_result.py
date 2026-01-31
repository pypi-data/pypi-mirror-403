from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.entra_id_tenant_model import EntraIDTenantModel
    from ..models.pagination_result import PaginationResult


T = TypeVar("T", bound="EntraIDTenantsResult")


@_attrs_define
class EntraIDTenantsResult:
    """Details on Microsoft Entra ID tenants.

    Attributes:
        data (Union[Unset, list['EntraIDTenantModel']]): Array of Microsoft Entra ID tenants.
        pagination (Union[Unset, PaginationResult]): Pagination settings.
    """

    data: Union[Unset, list["EntraIDTenantModel"]] = UNSET
    pagination: Union[Unset, "PaginationResult"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.data, Unset):
            data = []
            for data_item_data in self.data:
                data_item = data_item_data.to_dict()
                data.append(data_item)

        pagination: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.pagination, Unset):
            pagination = self.pagination.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if data is not UNSET:
            field_dict["data"] = data
        if pagination is not UNSET:
            field_dict["pagination"] = pagination

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.entra_id_tenant_model import EntraIDTenantModel
        from ..models.pagination_result import PaginationResult

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = EntraIDTenantModel.from_dict(data_item_data)

            data.append(data_item)

        _pagination = d.pop("pagination", UNSET)
        pagination: Union[Unset, PaginationResult]
        if isinstance(_pagination, Unset):
            pagination = UNSET
        else:
            pagination = PaginationResult.from_dict(_pagination)

        entra_id_tenants_result = cls(
            data=data,
            pagination=pagination,
        )

        entra_id_tenants_result.additional_properties = d
        return entra_id_tenants_result

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
