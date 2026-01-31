from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_instant_vi_vm_recovery_bios_uuid_policy_type import EInstantViVmRecoveryBiosUuidPolicyType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_object_model import AgentObjectModel
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.hyper_v_object_model import HyperVObjectModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="InstantViVMCustomizedRecoveryDestinationSpec")


@_attrs_define
class InstantViVMCustomizedRecoveryDestinationSpec:
    """Destination where the recovered VM resides. To get objects of the destination host, folder and resource pool, use
    the [Get Inventory Objects](Inventory-Browser#operation/GetInventoryObjects) request.

        Attributes:
            restored_vm_name (Union[Unset, str]): Restored VM name.
            destination_host (Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel',
                'VmwareObjectModel', Unset]): Inventory object properties.
            folder (Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel', 'VmwareObjectModel', Unset]):
                Inventory object properties.
            resource_pool (Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel', 'VmwareObjectModel',
                Unset]): Inventory object properties.
            bios_uuid_policy (Union[Unset, EInstantViVmRecoveryBiosUuidPolicyType]): BIOS UUID policy for the restored VM.
    """

    restored_vm_name: Union[Unset, str] = UNSET
    destination_host: Union[
        "AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel", Unset
    ] = UNSET
    folder: Union["AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel", Unset] = (
        UNSET
    )
    resource_pool: Union[
        "AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel", Unset
    ] = UNSET
    bios_uuid_policy: Union[Unset, EInstantViVmRecoveryBiosUuidPolicyType] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        restored_vm_name = self.restored_vm_name

        destination_host: Union[Unset, dict[str, Any]]
        if isinstance(self.destination_host, Unset):
            destination_host = UNSET
        elif isinstance(self.destination_host, VmwareObjectModel):
            destination_host = self.destination_host.to_dict()
        elif isinstance(self.destination_host, CloudDirectorObjectModel):
            destination_host = self.destination_host.to_dict()
        elif isinstance(self.destination_host, HyperVObjectModel):
            destination_host = self.destination_host.to_dict()
        else:
            destination_host = self.destination_host.to_dict()

        folder: Union[Unset, dict[str, Any]]
        if isinstance(self.folder, Unset):
            folder = UNSET
        elif isinstance(self.folder, VmwareObjectModel):
            folder = self.folder.to_dict()
        elif isinstance(self.folder, CloudDirectorObjectModel):
            folder = self.folder.to_dict()
        elif isinstance(self.folder, HyperVObjectModel):
            folder = self.folder.to_dict()
        else:
            folder = self.folder.to_dict()

        resource_pool: Union[Unset, dict[str, Any]]
        if isinstance(self.resource_pool, Unset):
            resource_pool = UNSET
        elif isinstance(self.resource_pool, VmwareObjectModel):
            resource_pool = self.resource_pool.to_dict()
        elif isinstance(self.resource_pool, CloudDirectorObjectModel):
            resource_pool = self.resource_pool.to_dict()
        elif isinstance(self.resource_pool, HyperVObjectModel):
            resource_pool = self.resource_pool.to_dict()
        else:
            resource_pool = self.resource_pool.to_dict()

        bios_uuid_policy: Union[Unset, str] = UNSET
        if not isinstance(self.bios_uuid_policy, Unset):
            bios_uuid_policy = self.bios_uuid_policy.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if restored_vm_name is not UNSET:
            field_dict["restoredVmName"] = restored_vm_name
        if destination_host is not UNSET:
            field_dict["destinationHost"] = destination_host
        if folder is not UNSET:
            field_dict["folder"] = folder
        if resource_pool is not UNSET:
            field_dict["resourcePool"] = resource_pool
        if bios_uuid_policy is not UNSET:
            field_dict["biosUuidPolicy"] = bios_uuid_policy

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_object_model import AgentObjectModel
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)
        restored_vm_name = d.pop("restoredVmName", UNSET)

        def _parse_destination_host(
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

        destination_host = _parse_destination_host(d.pop("destinationHost", UNSET))

        def _parse_folder(
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

        folder = _parse_folder(d.pop("folder", UNSET))

        def _parse_resource_pool(
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

        resource_pool = _parse_resource_pool(d.pop("resourcePool", UNSET))

        _bios_uuid_policy = d.pop("biosUuidPolicy", UNSET)
        bios_uuid_policy: Union[Unset, EInstantViVmRecoveryBiosUuidPolicyType]
        if isinstance(_bios_uuid_policy, Unset):
            bios_uuid_policy = UNSET
        else:
            bios_uuid_policy = EInstantViVmRecoveryBiosUuidPolicyType(_bios_uuid_policy)

        instant_vi_vm_customized_recovery_destination_spec = cls(
            restored_vm_name=restored_vm_name,
            destination_host=destination_host,
            folder=folder,
            resource_pool=resource_pool,
            bios_uuid_policy=bios_uuid_policy,
        )

        instant_vi_vm_customized_recovery_destination_spec.additional_properties = d
        return instant_vi_vm_customized_recovery_destination_spec

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
