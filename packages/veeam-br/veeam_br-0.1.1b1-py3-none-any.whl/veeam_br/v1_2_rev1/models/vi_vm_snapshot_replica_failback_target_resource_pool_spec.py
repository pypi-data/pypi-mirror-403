from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="ViVMSnapshotReplicaFailbackTargetResourcePoolSpec")


@_attrs_define
class ViVMSnapshotReplicaFailbackTargetResourcePoolSpec:
    """
    Attributes:
        replica_point_id (Union[Unset, UUID]): Restore point ID.
        resource_pool (Union['CloudDirectorObjectModel', 'VmwareObjectModel', Unset]): Inventory object properties.
    """

    replica_point_id: Union[Unset, UUID] = UNSET
    resource_pool: Union["CloudDirectorObjectModel", "VmwareObjectModel", Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.vmware_object_model import VmwareObjectModel

        replica_point_id: Union[Unset, str] = UNSET
        if not isinstance(self.replica_point_id, Unset):
            replica_point_id = str(self.replica_point_id)

        resource_pool: Union[Unset, dict[str, Any]]
        if isinstance(self.resource_pool, Unset):
            resource_pool = UNSET
        elif isinstance(self.resource_pool, VmwareObjectModel):
            resource_pool = self.resource_pool.to_dict()
        else:
            resource_pool = self.resource_pool.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if replica_point_id is not UNSET:
            field_dict["replicaPointId"] = replica_point_id
        if resource_pool is not UNSET:
            field_dict["resourcePool"] = resource_pool

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)
        _replica_point_id = d.pop("replicaPointId", UNSET)
        replica_point_id: Union[Unset, UUID]
        if isinstance(_replica_point_id, Unset):
            replica_point_id = UNSET
        else:
            replica_point_id = UUID(_replica_point_id)

        def _parse_resource_pool(data: object) -> Union["CloudDirectorObjectModel", "VmwareObjectModel", Unset]:
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

        resource_pool = _parse_resource_pool(d.pop("resourcePool", UNSET))

        vi_vm_snapshot_replica_failback_target_resource_pool_spec = cls(
            replica_point_id=replica_point_id,
            resource_pool=resource_pool,
        )

        vi_vm_snapshot_replica_failback_target_resource_pool_spec.additional_properties = d
        return vi_vm_snapshot_replica_failback_target_resource_pool_spec

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
