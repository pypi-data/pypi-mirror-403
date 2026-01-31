from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="ViVmSnapshotReplicaFailbackNetworkMappingModel")


@_attrs_define
class ViVmSnapshotReplicaFailbackNetworkMappingModel:
    """
    Attributes:
        source_network (Union['CloudDirectorObjectModel', 'VmwareObjectModel', Unset]): Inventory object properties.
        target_network (Union['CloudDirectorObjectModel', 'VmwareObjectModel', Unset]): Inventory object properties.
    """

    source_network: Union["CloudDirectorObjectModel", "VmwareObjectModel", Unset] = UNSET
    target_network: Union["CloudDirectorObjectModel", "VmwareObjectModel", Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.vmware_object_model import VmwareObjectModel

        source_network: Union[Unset, dict[str, Any]]
        if isinstance(self.source_network, Unset):
            source_network = UNSET
        elif isinstance(self.source_network, VmwareObjectModel):
            source_network = self.source_network.to_dict()
        else:
            source_network = self.source_network.to_dict()

        target_network: Union[Unset, dict[str, Any]]
        if isinstance(self.target_network, Unset):
            target_network = UNSET
        elif isinstance(self.target_network, VmwareObjectModel):
            target_network = self.target_network.to_dict()
        else:
            target_network = self.target_network.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if source_network is not UNSET:
            field_dict["sourceNetwork"] = source_network
        if target_network is not UNSET:
            field_dict["targetNetwork"] = target_network

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)

        def _parse_source_network(data: object) -> Union["CloudDirectorObjectModel", "VmwareObjectModel", Unset]:
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

        source_network = _parse_source_network(d.pop("sourceNetwork", UNSET))

        def _parse_target_network(data: object) -> Union["CloudDirectorObjectModel", "VmwareObjectModel", Unset]:
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

        target_network = _parse_target_network(d.pop("targetNetwork", UNSET))

        vi_vm_snapshot_replica_failback_network_mapping_model = cls(
            source_network=source_network,
            target_network=target_network,
        )

        vi_vm_snapshot_replica_failback_network_mapping_model.additional_properties = d
        return vi_vm_snapshot_replica_failback_network_mapping_model

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
