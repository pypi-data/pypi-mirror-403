from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="VmwareFcdQuickMigrationSpec")


@_attrs_define
class VmwareFcdQuickMigrationSpec:
    """
    Attributes:
        target_datastore (Union['CloudDirectorObjectModel', 'VmwareObjectModel']): Inventory object properties.
        mounted_disk_names (Union[Unset, list[str]]): Array of disks that will be migrated to the `targetDatastore`
            associated with the `storagePolicy`.
        storage_policy (Union['CloudDirectorObjectModel', 'VmwareObjectModel', Unset]): Inventory object properties.
    """

    target_datastore: Union["CloudDirectorObjectModel", "VmwareObjectModel"]
    mounted_disk_names: Union[Unset, list[str]] = UNSET
    storage_policy: Union["CloudDirectorObjectModel", "VmwareObjectModel", Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.vmware_object_model import VmwareObjectModel

        target_datastore: dict[str, Any]
        if isinstance(self.target_datastore, VmwareObjectModel):
            target_datastore = self.target_datastore.to_dict()
        else:
            target_datastore = self.target_datastore.to_dict()

        mounted_disk_names: Union[Unset, list[str]] = UNSET
        if not isinstance(self.mounted_disk_names, Unset):
            mounted_disk_names = self.mounted_disk_names

        storage_policy: Union[Unset, dict[str, Any]]
        if isinstance(self.storage_policy, Unset):
            storage_policy = UNSET
        elif isinstance(self.storage_policy, VmwareObjectModel):
            storage_policy = self.storage_policy.to_dict()
        else:
            storage_policy = self.storage_policy.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "targetDatastore": target_datastore,
            }
        )
        if mounted_disk_names is not UNSET:
            field_dict["mountedDiskNames"] = mounted_disk_names
        if storage_policy is not UNSET:
            field_dict["storagePolicy"] = storage_policy

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)

        def _parse_target_datastore(data: object) -> Union["CloudDirectorObjectModel", "VmwareObjectModel"]:
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

        target_datastore = _parse_target_datastore(d.pop("targetDatastore"))

        mounted_disk_names = cast(list[str], d.pop("mountedDiskNames", UNSET))

        def _parse_storage_policy(data: object) -> Union["CloudDirectorObjectModel", "VmwareObjectModel", Unset]:
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

        storage_policy = _parse_storage_policy(d.pop("storagePolicy", UNSET))

        vmware_fcd_quick_migration_spec = cls(
            target_datastore=target_datastore,
            mounted_disk_names=mounted_disk_names,
            storage_policy=storage_policy,
        )

        vmware_fcd_quick_migration_spec.additional_properties = d
        return vmware_fcd_quick_migration_spec

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
