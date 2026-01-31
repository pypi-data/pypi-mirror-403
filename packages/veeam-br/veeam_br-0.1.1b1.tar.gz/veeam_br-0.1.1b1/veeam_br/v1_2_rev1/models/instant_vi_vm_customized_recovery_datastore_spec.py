from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="InstantViVMCustomizedRecoveryDatastoreSpec")


@_attrs_define
class InstantViVMCustomizedRecoveryDatastoreSpec:
    """Datastore that keeps redo logs with changes that take place while a VM is running from a backup. To get a datastore
    object, use the [Get Inventory Objects](#tag/Inventory-Browser/operation/GetInventoryObjects) request.

        Attributes:
            redirect_enabled (bool): If `true`, redo logs are redirected to `cacheDatastore`.
            cache_datastore (Union['CloudDirectorObjectModel', 'VmwareObjectModel', Unset]): Inventory object properties.
    """

    redirect_enabled: bool
    cache_datastore: Union["CloudDirectorObjectModel", "VmwareObjectModel", Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.vmware_object_model import VmwareObjectModel

        redirect_enabled = self.redirect_enabled

        cache_datastore: Union[Unset, dict[str, Any]]
        if isinstance(self.cache_datastore, Unset):
            cache_datastore = UNSET
        elif isinstance(self.cache_datastore, VmwareObjectModel):
            cache_datastore = self.cache_datastore.to_dict()
        else:
            cache_datastore = self.cache_datastore.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "redirectEnabled": redirect_enabled,
            }
        )
        if cache_datastore is not UNSET:
            field_dict["cacheDatastore"] = cache_datastore

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)
        redirect_enabled = d.pop("redirectEnabled")

        def _parse_cache_datastore(data: object) -> Union["CloudDirectorObjectModel", "VmwareObjectModel", Unset]:
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

        cache_datastore = _parse_cache_datastore(d.pop("cacheDatastore", UNSET))

        instant_vi_vm_customized_recovery_datastore_spec = cls(
            redirect_enabled=redirect_enabled,
            cache_datastore=cache_datastore,
        )

        instant_vi_vm_customized_recovery_datastore_spec.additional_properties = d
        return instant_vi_vm_customized_recovery_datastore_spec

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
