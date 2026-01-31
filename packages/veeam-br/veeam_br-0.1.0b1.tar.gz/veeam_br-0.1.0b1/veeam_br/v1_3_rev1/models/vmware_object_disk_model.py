from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_vmware_disks_type_to_process import EVmwareDisksTypeToProcess
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_object_model import AgentObjectModel
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.hyper_v_object_model import HyperVObjectModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="VmwareObjectDiskModel")


@_attrs_define
class VmwareObjectDiskModel:
    """Disk settings for VMware vSphere object.

    Attributes:
        vm_object (Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel', 'VmwareObjectModel']):
            Inventory object properties.
        disks_to_process (EVmwareDisksTypeToProcess): Type of disk selection.
        disks (list[str]): Array of disks.
        remove_from_vm_configuration (Union[Unset, bool]): If `true`, the disk is removed from VM configuration.
    """

    vm_object: Union["AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel"]
    disks_to_process: EVmwareDisksTypeToProcess
    disks: list[str]
    remove_from_vm_configuration: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        vm_object: dict[str, Any]
        if isinstance(self.vm_object, VmwareObjectModel):
            vm_object = self.vm_object.to_dict()
        elif isinstance(self.vm_object, CloudDirectorObjectModel):
            vm_object = self.vm_object.to_dict()
        elif isinstance(self.vm_object, HyperVObjectModel):
            vm_object = self.vm_object.to_dict()
        else:
            vm_object = self.vm_object.to_dict()

        disks_to_process = self.disks_to_process.value

        disks = self.disks

        remove_from_vm_configuration = self.remove_from_vm_configuration

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "vmObject": vm_object,
                "disksToProcess": disks_to_process,
                "disks": disks,
            }
        )
        if remove_from_vm_configuration is not UNSET:
            field_dict["removeFromVMConfiguration"] = remove_from_vm_configuration

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_object_model import AgentObjectModel
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)

        def _parse_vm_object(
            data: object,
        ) -> Union["AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel"]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_inventory_object_model_type_0 = VmwareObjectModel.from_dict(data)

                return componentsschemas_inventory_object_model_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_inventory_object_model_type_1 = CloudDirectorObjectModel.from_dict(data)

                return componentsschemas_inventory_object_model_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_inventory_object_model_type_2 = HyperVObjectModel.from_dict(data)

                return componentsschemas_inventory_object_model_type_2
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_inventory_object_model_type_3 = AgentObjectModel.from_dict(data)

            return componentsschemas_inventory_object_model_type_3

        vm_object = _parse_vm_object(d.pop("vmObject"))

        disks_to_process = EVmwareDisksTypeToProcess(d.pop("disksToProcess"))

        disks = cast(list[str], d.pop("disks"))

        remove_from_vm_configuration = d.pop("removeFromVMConfiguration", UNSET)

        vmware_object_disk_model = cls(
            vm_object=vm_object,
            disks_to_process=disks_to_process,
            disks=disks,
            remove_from_vm_configuration=remove_from_vm_configuration,
        )

        vmware_object_disk_model.additional_properties = d
        return vmware_object_disk_model

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
