from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_object_model import AgentObjectModel
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.hyper_v_object_model import HyperVObjectModel
    from ..models.vi_vm_snapshot_replica_failback_target_disk_spec import ViVmSnapshotReplicaFailbackTargetDiskSpec
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="ViVMSnapshotReplicaFailbackTargetDatastoreSpec")


@_attrs_define
class ViVMSnapshotReplicaFailbackTargetDatastoreSpec:
    """Target datastore settings.

    Attributes:
        vm_object (Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel', 'VmwareObjectModel',
            Unset]): Inventory object properties.
        disks (Union[Unset, list['ViVmSnapshotReplicaFailbackTargetDiskSpec']]): Array of disks that you want to store
            on the specified datastore.
    """

    vm_object: Union[
        "AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel", Unset
    ] = UNSET
    disks: Union[Unset, list["ViVmSnapshotReplicaFailbackTargetDiskSpec"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        vm_object: Union[Unset, dict[str, Any]]
        if isinstance(self.vm_object, Unset):
            vm_object = UNSET
        elif isinstance(self.vm_object, VmwareObjectModel):
            vm_object = self.vm_object.to_dict()
        elif isinstance(self.vm_object, CloudDirectorObjectModel):
            vm_object = self.vm_object.to_dict()
        elif isinstance(self.vm_object, HyperVObjectModel):
            vm_object = self.vm_object.to_dict()
        else:
            vm_object = self.vm_object.to_dict()

        disks: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.disks, Unset):
            disks = []
            for disks_item_data in self.disks:
                disks_item = disks_item_data.to_dict()
                disks.append(disks_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if vm_object is not UNSET:
            field_dict["vmObject"] = vm_object
        if disks is not UNSET:
            field_dict["disks"] = disks

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_object_model import AgentObjectModel
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vi_vm_snapshot_replica_failback_target_disk_spec import ViVmSnapshotReplicaFailbackTargetDiskSpec
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)

        def _parse_vm_object(
            data: object,
        ) -> Union["AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel", Unset]:
            if isinstance(data, Unset):
                return data
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

        vm_object = _parse_vm_object(d.pop("vmObject", UNSET))

        disks = []
        _disks = d.pop("disks", UNSET)
        for disks_item_data in _disks or []:
            disks_item = ViVmSnapshotReplicaFailbackTargetDiskSpec.from_dict(disks_item_data)

            disks.append(disks_item)

        vi_vm_snapshot_replica_failback_target_datastore_spec = cls(
            vm_object=vm_object,
            disks=disks,
        )

        vi_vm_snapshot_replica_failback_target_datastore_spec.additional_properties = d
        return vi_vm_snapshot_replica_failback_target_datastore_spec

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
