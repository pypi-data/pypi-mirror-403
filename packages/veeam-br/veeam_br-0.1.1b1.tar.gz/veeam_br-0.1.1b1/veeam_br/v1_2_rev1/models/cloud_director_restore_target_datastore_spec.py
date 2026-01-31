from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="CloudDirectorRestoreTargetDatastoreSpec")


@_attrs_define
class CloudDirectorRestoreTargetDatastoreSpec:
    """Datastore and storage for the recovered VM. To get datastore and storage policy objects, use the [Get Inventory
    Objects](#tag/Inventory-Browser/operation/GetInventoryObjects) request.

        Attributes:
            datastore (Union['CloudDirectorObjectModel', 'VmwareObjectModel']): Inventory object properties.
            storage_policy (Union['CloudDirectorObjectModel', 'VmwareObjectModel', Unset]): Inventory object properties.
    """

    datastore: Union["CloudDirectorObjectModel", "VmwareObjectModel"]
    storage_policy: Union["CloudDirectorObjectModel", "VmwareObjectModel", Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.vmware_object_model import VmwareObjectModel

        datastore: dict[str, Any]
        if isinstance(self.datastore, VmwareObjectModel):
            datastore = self.datastore.to_dict()
        else:
            datastore = self.datastore.to_dict()

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
                "datastore": datastore,
            }
        )
        if storage_policy is not UNSET:
            field_dict["storagePolicy"] = storage_policy

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)

        def _parse_datastore(data: object) -> Union["CloudDirectorObjectModel", "VmwareObjectModel"]:
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

        datastore = _parse_datastore(d.pop("datastore"))

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

        cloud_director_restore_target_datastore_spec = cls(
            datastore=datastore,
            storage_policy=storage_policy,
        )

        cloud_director_restore_target_datastore_spec.additional_properties = d
        return cloud_director_restore_target_datastore_spec

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
