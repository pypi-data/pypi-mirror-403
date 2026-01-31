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
    from ..models.vmware_fcd_instant_recovery_disk_spec import VmwareFcdInstantRecoveryDiskSpec
    from ..models.vmware_fcd_write_cache_spec import VmwareFcdWriteCacheSpec
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="VmwareFcdInstantRecoverySpec")


@_attrs_define
class VmwareFcdInstantRecoverySpec:
    """Instant FCD Recovery configuration:<ul> <li>Restore point ID</li> <li>Destination cluster</li> <li>Disks for
    restore</li> <li>Write cache</li></ul>

        Attributes:
            restore_point_id (UUID): ID of the restore point.
            destination_cluster (Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel',
                'VmwareObjectModel']): Inventory object properties.
            disks_mapping (list['VmwareFcdInstantRecoveryDiskSpec']): Array of disks for restore.
            write_cache (Union[Unset, VmwareFcdWriteCacheSpec]): Write cache for recovered disks.
    """

    restore_point_id: UUID
    destination_cluster: Union["AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel"]
    disks_mapping: list["VmwareFcdInstantRecoveryDiskSpec"]
    write_cache: Union[Unset, "VmwareFcdWriteCacheSpec"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        restore_point_id = str(self.restore_point_id)

        destination_cluster: dict[str, Any]
        if isinstance(self.destination_cluster, VmwareObjectModel):
            destination_cluster = self.destination_cluster.to_dict()
        elif isinstance(self.destination_cluster, CloudDirectorObjectModel):
            destination_cluster = self.destination_cluster.to_dict()
        elif isinstance(self.destination_cluster, HyperVObjectModel):
            destination_cluster = self.destination_cluster.to_dict()
        else:
            destination_cluster = self.destination_cluster.to_dict()

        disks_mapping = []
        for disks_mapping_item_data in self.disks_mapping:
            disks_mapping_item = disks_mapping_item_data.to_dict()
            disks_mapping.append(disks_mapping_item)

        write_cache: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.write_cache, Unset):
            write_cache = self.write_cache.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "restorePointId": restore_point_id,
                "destinationCluster": destination_cluster,
                "disksMapping": disks_mapping,
            }
        )
        if write_cache is not UNSET:
            field_dict["writeCache"] = write_cache

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_object_model import AgentObjectModel
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_fcd_instant_recovery_disk_spec import VmwareFcdInstantRecoveryDiskSpec
        from ..models.vmware_fcd_write_cache_spec import VmwareFcdWriteCacheSpec
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)
        restore_point_id = UUID(d.pop("restorePointId"))

        def _parse_destination_cluster(
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

        destination_cluster = _parse_destination_cluster(d.pop("destinationCluster"))

        disks_mapping = []
        _disks_mapping = d.pop("disksMapping")
        for disks_mapping_item_data in _disks_mapping:
            disks_mapping_item = VmwareFcdInstantRecoveryDiskSpec.from_dict(disks_mapping_item_data)

            disks_mapping.append(disks_mapping_item)

        _write_cache = d.pop("writeCache", UNSET)
        write_cache: Union[Unset, VmwareFcdWriteCacheSpec]
        if isinstance(_write_cache, Unset):
            write_cache = UNSET
        else:
            write_cache = VmwareFcdWriteCacheSpec.from_dict(_write_cache)

        vmware_fcd_instant_recovery_spec = cls(
            restore_point_id=restore_point_id,
            destination_cluster=destination_cluster,
            disks_mapping=disks_mapping,
            write_cache=write_cache,
        )

        vmware_fcd_instant_recovery_spec.additional_properties = d
        return vmware_fcd_instant_recovery_spec

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
