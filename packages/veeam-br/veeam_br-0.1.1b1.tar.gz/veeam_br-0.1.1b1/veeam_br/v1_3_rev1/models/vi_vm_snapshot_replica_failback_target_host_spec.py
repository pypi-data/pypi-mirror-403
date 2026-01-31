from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_object_model import AgentObjectModel
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.hyper_v_object_model import HyperVObjectModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="ViVMSnapshotReplicaFailbackTargetHostSpec")


@_attrs_define
class ViVMSnapshotReplicaFailbackTargetHostSpec:
    """Target host settings.

    Attributes:
        replica_point_id (Union[Unset, UUID]): Restore point ID.
        host (Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel', 'VmwareObjectModel', Unset]):
            Inventory object properties.
    """

    replica_point_id: Union[Unset, UUID] = UNSET
    host: Union["AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel", Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        replica_point_id: Union[Unset, str] = UNSET
        if not isinstance(self.replica_point_id, Unset):
            replica_point_id = str(self.replica_point_id)

        host: Union[Unset, dict[str, Any]]
        if isinstance(self.host, Unset):
            host = UNSET
        elif isinstance(self.host, VmwareObjectModel):
            host = self.host.to_dict()
        elif isinstance(self.host, CloudDirectorObjectModel):
            host = self.host.to_dict()
        elif isinstance(self.host, HyperVObjectModel):
            host = self.host.to_dict()
        else:
            host = self.host.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if replica_point_id is not UNSET:
            field_dict["replicaPointId"] = replica_point_id
        if host is not UNSET:
            field_dict["host"] = host

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_object_model import AgentObjectModel
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)
        _replica_point_id = d.pop("replicaPointId", UNSET)
        replica_point_id: Union[Unset, UUID]
        if isinstance(_replica_point_id, Unset):
            replica_point_id = UNSET
        else:
            replica_point_id = UUID(_replica_point_id)

        def _parse_host(
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

        host = _parse_host(d.pop("host", UNSET))

        vi_vm_snapshot_replica_failback_target_host_spec = cls(
            replica_point_id=replica_point_id,
            host=host,
        )

        vi_vm_snapshot_replica_failback_target_host_spec.additional_properties = d
        return vi_vm_snapshot_replica_failback_target_host_spec

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
