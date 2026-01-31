from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_disk_creation_mode import EDiskCreationMode
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="RestoreTargetDatastoreSpec")


@_attrs_define
class RestoreTargetDatastoreSpec:
    """Destination datastore.

    Attributes:
        disk_name (str):
        datastore (Union['CloudDirectorObjectModel', 'VmwareObjectModel']): Inventory object properties.
        disk_type (Union[Unset, EDiskCreationMode]): Disk provisioning type for the recovered VM.
    """

    disk_name: str
    datastore: Union["CloudDirectorObjectModel", "VmwareObjectModel"]
    disk_type: Union[Unset, EDiskCreationMode] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.vmware_object_model import VmwareObjectModel

        disk_name = self.disk_name

        datastore: dict[str, Any]
        if isinstance(self.datastore, VmwareObjectModel):
            datastore = self.datastore.to_dict()
        else:
            datastore = self.datastore.to_dict()

        disk_type: Union[Unset, str] = UNSET
        if not isinstance(self.disk_type, Unset):
            disk_type = self.disk_type.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "diskName": disk_name,
                "datastore": datastore,
            }
        )
        if disk_type is not UNSET:
            field_dict["diskType"] = disk_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)
        disk_name = d.pop("diskName")

        def _parse_datastore(data: object) -> Union["CloudDirectorObjectModel", "VmwareObjectModel"]:
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

        datastore = _parse_datastore(d.pop("datastore"))

        _disk_type = d.pop("diskType", UNSET)
        disk_type: Union[Unset, EDiskCreationMode]
        if isinstance(_disk_type, Unset):
            disk_type = UNSET
        else:
            disk_type = EDiskCreationMode(_disk_type)

        restore_target_datastore_spec = cls(
            disk_name=disk_name,
            datastore=datastore,
            disk_type=disk_type,
        )

        restore_target_datastore_spec.additional_properties = d
        return restore_target_datastore_spec

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
