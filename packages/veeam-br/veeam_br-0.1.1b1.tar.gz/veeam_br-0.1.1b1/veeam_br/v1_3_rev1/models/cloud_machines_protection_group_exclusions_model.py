from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cloud_machine_model import CloudMachineModel
    from ..models.cloud_region_model import CloudRegionModel
    from ..models.cloud_tag_model import CloudTagModel


T = TypeVar("T", bound="CloudMachinesProtectionGroupExclusionsModel")


@_attrs_define
class CloudMachinesProtectionGroupExclusionsModel:
    """Exclusion settings for cloud objects.

    Attributes:
        exclude_selected_objects (Union[Unset, bool]): If `true`, the selected objects will be excluded from processing.
        excluded_objects (Union[Unset, list[Union['CloudMachineModel', 'CloudRegionModel', 'CloudTagModel']]]): Array of
            excluded objects.
    """

    exclude_selected_objects: Union[Unset, bool] = UNSET
    excluded_objects: Union[Unset, list[Union["CloudMachineModel", "CloudRegionModel", "CloudTagModel"]]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.cloud_machine_model import CloudMachineModel
        from ..models.cloud_region_model import CloudRegionModel

        exclude_selected_objects = self.exclude_selected_objects

        excluded_objects: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.excluded_objects, Unset):
            excluded_objects = []
            for excluded_objects_item_data in self.excluded_objects:
                excluded_objects_item: dict[str, Any]
                if isinstance(excluded_objects_item_data, CloudRegionModel):
                    excluded_objects_item = excluded_objects_item_data.to_dict()
                elif isinstance(excluded_objects_item_data, CloudMachineModel):
                    excluded_objects_item = excluded_objects_item_data.to_dict()
                else:
                    excluded_objects_item = excluded_objects_item_data.to_dict()

                excluded_objects.append(excluded_objects_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if exclude_selected_objects is not UNSET:
            field_dict["excludeSelectedObjects"] = exclude_selected_objects
        if excluded_objects is not UNSET:
            field_dict["excludedObjects"] = excluded_objects

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_machine_model import CloudMachineModel
        from ..models.cloud_region_model import CloudRegionModel
        from ..models.cloud_tag_model import CloudTagModel

        d = dict(src_dict)
        exclude_selected_objects = d.pop("excludeSelectedObjects", UNSET)

        excluded_objects = []
        _excluded_objects = d.pop("excludedObjects", UNSET)
        for excluded_objects_item_data in _excluded_objects or []:

            def _parse_excluded_objects_item(
                data: object,
            ) -> Union["CloudMachineModel", "CloudRegionModel", "CloudTagModel"]:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_cloud_machines_protection_group_objects_model_type_0 = CloudRegionModel.from_dict(
                        data
                    )

                    return componentsschemas_cloud_machines_protection_group_objects_model_type_0
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_cloud_machines_protection_group_objects_model_type_1 = (
                        CloudMachineModel.from_dict(data)
                    )

                    return componentsschemas_cloud_machines_protection_group_objects_model_type_1
                except:  # noqa: E722
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_cloud_machines_protection_group_objects_model_type_2 = CloudTagModel.from_dict(data)

                return componentsschemas_cloud_machines_protection_group_objects_model_type_2

            excluded_objects_item = _parse_excluded_objects_item(excluded_objects_item_data)

            excluded_objects.append(excluded_objects_item)

        cloud_machines_protection_group_exclusions_model = cls(
            exclude_selected_objects=exclude_selected_objects,
            excluded_objects=excluded_objects,
        )

        cloud_machines_protection_group_exclusions_model.additional_properties = d
        return cloud_machines_protection_group_exclusions_model

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
