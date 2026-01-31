from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.restore_target_datastore_spec import RestoreTargetDatastoreSpec
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="RestoreTargetDatastoresSpec")


@_attrs_define
class RestoreTargetDatastoresSpec:
    """Destination datastore.

    Attributes:
        configuration_file_datastore (Union['CloudDirectorObjectModel', 'VmwareObjectModel', Unset]): Inventory object
            properties.
        disk_mappings (Union[Unset, list['RestoreTargetDatastoreSpec']]):
    """

    configuration_file_datastore: Union["CloudDirectorObjectModel", "VmwareObjectModel", Unset] = UNSET
    disk_mappings: Union[Unset, list["RestoreTargetDatastoreSpec"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.vmware_object_model import VmwareObjectModel

        configuration_file_datastore: Union[Unset, dict[str, Any]]
        if isinstance(self.configuration_file_datastore, Unset):
            configuration_file_datastore = UNSET
        elif isinstance(self.configuration_file_datastore, VmwareObjectModel):
            configuration_file_datastore = self.configuration_file_datastore.to_dict()
        else:
            configuration_file_datastore = self.configuration_file_datastore.to_dict()

        disk_mappings: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.disk_mappings, Unset):
            disk_mappings = []
            for disk_mappings_item_data in self.disk_mappings:
                disk_mappings_item = disk_mappings_item_data.to_dict()
                disk_mappings.append(disk_mappings_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if configuration_file_datastore is not UNSET:
            field_dict["configurationFileDatastore"] = configuration_file_datastore
        if disk_mappings is not UNSET:
            field_dict["diskMappings"] = disk_mappings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.restore_target_datastore_spec import RestoreTargetDatastoreSpec
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)

        def _parse_configuration_file_datastore(
            data: object,
        ) -> Union["CloudDirectorObjectModel", "VmwareObjectModel", Unset]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_inventory_object_model_type_0 = VmwareObjectModel.from_dict(data)

                return componentsschemas_inventory_object_model_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_inventory_object_model_type_1 = CloudDirectorObjectModel.from_dict(data)

            return componentsschemas_inventory_object_model_type_1

        configuration_file_datastore = _parse_configuration_file_datastore(d.pop("configurationFileDatastore", UNSET))

        disk_mappings = []
        _disk_mappings = d.pop("diskMappings", UNSET)
        for disk_mappings_item_data in _disk_mappings or []:
            disk_mappings_item = RestoreTargetDatastoreSpec.from_dict(disk_mappings_item_data)

            disk_mappings.append(disk_mappings_item)

        restore_target_datastores_spec = cls(
            configuration_file_datastore=configuration_file_datastore,
            disk_mappings=disk_mappings,
        )

        restore_target_datastores_spec.additional_properties = d
        return restore_target_datastores_spec

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
