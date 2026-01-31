from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="ReplicaMappingRuleModel")


@_attrs_define
class ReplicaMappingRuleModel:
    """Replica mapping rule.

    Attributes:
        original_vm (Union['CloudDirectorObjectModel', 'VmwareObjectModel']): Inventory object properties.
        replica_vm (Union['CloudDirectorObjectModel', 'VmwareObjectModel']): Inventory object properties.
    """

    original_vm: Union["CloudDirectorObjectModel", "VmwareObjectModel"]
    replica_vm: Union["CloudDirectorObjectModel", "VmwareObjectModel"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.vmware_object_model import VmwareObjectModel

        original_vm: dict[str, Any]
        if isinstance(self.original_vm, VmwareObjectModel):
            original_vm = self.original_vm.to_dict()
        else:
            original_vm = self.original_vm.to_dict()

        replica_vm: dict[str, Any]
        if isinstance(self.replica_vm, VmwareObjectModel):
            replica_vm = self.replica_vm.to_dict()
        else:
            replica_vm = self.replica_vm.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "originalVM": original_vm,
                "replicaVM": replica_vm,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)

        def _parse_original_vm(data: object) -> Union["CloudDirectorObjectModel", "VmwareObjectModel"]:
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

        original_vm = _parse_original_vm(d.pop("originalVM"))

        def _parse_replica_vm(data: object) -> Union["CloudDirectorObjectModel", "VmwareObjectModel"]:
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

        replica_vm = _parse_replica_vm(d.pop("replicaVM"))

        replica_mapping_rule_model = cls(
            original_vm=original_vm,
            replica_vm=replica_vm,
        )

        replica_mapping_rule_model.additional_properties = d
        return replica_mapping_rule_model

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
