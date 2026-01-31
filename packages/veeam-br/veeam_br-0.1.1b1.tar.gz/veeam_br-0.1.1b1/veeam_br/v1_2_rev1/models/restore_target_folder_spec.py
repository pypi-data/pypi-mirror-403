from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="RestoreTargetFolderSpec")


@_attrs_define
class RestoreTargetFolderSpec:
    """Destination VM folder.

    Attributes:
        folder (Union['CloudDirectorObjectModel', 'VmwareObjectModel']): Inventory object properties.
        vm_name (Union[Unset, str]): Name of the restored VM. Note that if you do not specify a value for this property,
            Veeam Backup & Replication will use the original VM name.
        restore_vm_tags (Union[Unset, bool]): If `true`, Veeam Backup & Replication restores tags that were assigned to
            the original VMs, and assigns them to the restored VMs.
    """

    folder: Union["CloudDirectorObjectModel", "VmwareObjectModel"]
    vm_name: Union[Unset, str] = UNSET
    restore_vm_tags: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.vmware_object_model import VmwareObjectModel

        folder: dict[str, Any]
        if isinstance(self.folder, VmwareObjectModel):
            folder = self.folder.to_dict()
        else:
            folder = self.folder.to_dict()

        vm_name = self.vm_name

        restore_vm_tags = self.restore_vm_tags

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "folder": folder,
            }
        )
        if vm_name is not UNSET:
            field_dict["vmName"] = vm_name
        if restore_vm_tags is not UNSET:
            field_dict["restoreVmTags"] = restore_vm_tags

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)

        def _parse_folder(data: object) -> Union["CloudDirectorObjectModel", "VmwareObjectModel"]:
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

        folder = _parse_folder(d.pop("folder"))

        vm_name = d.pop("vmName", UNSET)

        restore_vm_tags = d.pop("restoreVmTags", UNSET)

        restore_target_folder_spec = cls(
            folder=folder,
            vm_name=vm_name,
            restore_vm_tags=restore_vm_tags,
        )

        restore_target_folder_spec.additional_properties = d
        return restore_target_folder_spec

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
