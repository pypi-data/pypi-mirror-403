from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_cloud_credentials_type import ECloudCredentialsType
from ..types import UNSET, Unset

T = TypeVar("T", bound="CloudCredentialsExportSpec")


@_attrs_define
class CloudCredentialsExportSpec:
    """
    Attributes:
        ids (Union[Unset, list[UUID]]): Array of cloud credentials IDs that you want to export.
        types (Union[Unset, list[ECloudCredentialsType]]): Array of cloud credentials types that you want to export.
        names (Union[Unset, list[str]]): Array of cloud credentials user names. Wildcard characters are supported.
    """

    ids: Union[Unset, list[UUID]] = UNSET
    types: Union[Unset, list[ECloudCredentialsType]] = UNSET
    names: Union[Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.ids, Unset):
            ids = []
            for ids_item_data in self.ids:
                ids_item = str(ids_item_data)
                ids.append(ids_item)

        types: Union[Unset, list[str]] = UNSET
        if not isinstance(self.types, Unset):
            types = []
            for types_item_data in self.types:
                types_item = types_item_data.value
                types.append(types_item)

        names: Union[Unset, list[str]] = UNSET
        if not isinstance(self.names, Unset):
            names = self.names

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if ids is not UNSET:
            field_dict["ids"] = ids
        if types is not UNSET:
            field_dict["types"] = types
        if names is not UNSET:
            field_dict["names"] = names

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        ids = []
        _ids = d.pop("ids", UNSET)
        for ids_item_data in _ids or []:
            ids_item = UUID(ids_item_data)

            ids.append(ids_item)

        types = []
        _types = d.pop("types", UNSET)
        for types_item_data in _types or []:
            types_item = ECloudCredentialsType(types_item_data)

            types.append(types_item)

        names = cast(list[str], d.pop("names", UNSET))

        cloud_credentials_export_spec = cls(
            ids=ids,
            types=types,
            names=names,
        )

        cloud_credentials_export_spec.additional_properties = d
        return cloud_credentials_export_spec

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
