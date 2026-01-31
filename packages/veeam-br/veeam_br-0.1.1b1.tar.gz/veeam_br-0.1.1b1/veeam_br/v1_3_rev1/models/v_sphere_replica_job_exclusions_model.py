from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_object_model import AgentObjectModel
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.hyper_v_object_model import HyperVObjectModel
    from ..models.vmware_object_disk_model import VmwareObjectDiskModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="VSphereReplicaJobExclusionsModel")


@_attrs_define
class VSphereReplicaJobExclusionsModel:
    """Objects excluded from the job.

    Attributes:
        vms (Union[Unset, list[Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel',
            'VmwareObjectModel']]]): Array of VMs excluded from the job.
        disks (Union[Unset, list['VmwareObjectDiskModel']]): Array of VM disks excluded from the job.
    """

    vms: Union[
        Unset, list[Union["AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel"]]
    ] = UNSET
    disks: Union[Unset, list["VmwareObjectDiskModel"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        vms: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.vms, Unset):
            vms = []
            for vms_item_data in self.vms:
                vms_item: dict[str, Any]
                if isinstance(vms_item_data, VmwareObjectModel):
                    vms_item = vms_item_data.to_dict()
                elif isinstance(vms_item_data, CloudDirectorObjectModel):
                    vms_item = vms_item_data.to_dict()
                elif isinstance(vms_item_data, HyperVObjectModel):
                    vms_item = vms_item_data.to_dict()
                else:
                    vms_item = vms_item_data.to_dict()

                vms.append(vms_item)

        disks: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.disks, Unset):
            disks = []
            for disks_item_data in self.disks:
                disks_item = disks_item_data.to_dict()
                disks.append(disks_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if vms is not UNSET:
            field_dict["vms"] = vms
        if disks is not UNSET:
            field_dict["disks"] = disks

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_object_model import AgentObjectModel
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_disk_model import VmwareObjectDiskModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)
        vms = []
        _vms = d.pop("vms", UNSET)
        for vms_item_data in _vms or []:

            def _parse_vms_item(
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

            vms_item = _parse_vms_item(vms_item_data)

            vms.append(vms_item)

        disks = []
        _disks = d.pop("disks", UNSET)
        for disks_item_data in _disks or []:
            disks_item = VmwareObjectDiskModel.from_dict(disks_item_data)

            disks.append(disks_item)

        v_sphere_replica_job_exclusions_model = cls(
            vms=vms,
            disks=disks,
        )

        v_sphere_replica_job_exclusions_model.additional_properties = d
        return v_sphere_replica_job_exclusions_model

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
