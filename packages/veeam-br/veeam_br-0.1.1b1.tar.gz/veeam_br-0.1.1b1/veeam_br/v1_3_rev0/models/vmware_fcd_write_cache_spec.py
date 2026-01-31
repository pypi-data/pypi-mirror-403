from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_object_model import AgentObjectModel
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.hyper_v_object_model import HyperVObjectModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="VmwareFcdWriteCacheSpec")


@_attrs_define
class VmwareFcdWriteCacheSpec:
    """Write cache for recovered disks.

    Attributes:
        redirect_is_enabled (bool): If `true`, cache redirection is enabled. In this case, all changes made to the
            recovered disks while the Instant FCD Recovery is active are redirected to the specified `cacheDatastore`
            associated with the `storagePolicy`.
        cache_datastore (Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel', 'VmwareObjectModel',
            Unset]): Inventory object properties.
        storage_policy (Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel', 'VmwareObjectModel',
            Unset]): Inventory object properties.
    """

    redirect_is_enabled: bool
    cache_datastore: Union[
        "AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel", Unset
    ] = UNSET
    storage_policy: Union[
        "AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel", Unset
    ] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        redirect_is_enabled = self.redirect_is_enabled

        cache_datastore: Union[Unset, dict[str, Any]]
        if isinstance(self.cache_datastore, Unset):
            cache_datastore = UNSET
        elif isinstance(self.cache_datastore, VmwareObjectModel):
            cache_datastore = self.cache_datastore.to_dict()
        elif isinstance(self.cache_datastore, CloudDirectorObjectModel):
            cache_datastore = self.cache_datastore.to_dict()
        elif isinstance(self.cache_datastore, HyperVObjectModel):
            cache_datastore = self.cache_datastore.to_dict()
        else:
            cache_datastore = self.cache_datastore.to_dict()

        storage_policy: Union[Unset, dict[str, Any]]
        if isinstance(self.storage_policy, Unset):
            storage_policy = UNSET
        elif isinstance(self.storage_policy, VmwareObjectModel):
            storage_policy = self.storage_policy.to_dict()
        elif isinstance(self.storage_policy, CloudDirectorObjectModel):
            storage_policy = self.storage_policy.to_dict()
        elif isinstance(self.storage_policy, HyperVObjectModel):
            storage_policy = self.storage_policy.to_dict()
        else:
            storage_policy = self.storage_policy.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "redirectIsEnabled": redirect_is_enabled,
            }
        )
        if cache_datastore is not UNSET:
            field_dict["cacheDatastore"] = cache_datastore
        if storage_policy is not UNSET:
            field_dict["storagePolicy"] = storage_policy

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_object_model import AgentObjectModel
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)
        redirect_is_enabled = d.pop("redirectIsEnabled")

        def _parse_cache_datastore(
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

        cache_datastore = _parse_cache_datastore(d.pop("cacheDatastore", UNSET))

        def _parse_storage_policy(
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

        storage_policy = _parse_storage_policy(d.pop("storagePolicy", UNSET))

        vmware_fcd_write_cache_spec = cls(
            redirect_is_enabled=redirect_is_enabled,
            cache_datastore=cache_datastore,
            storage_policy=storage_policy,
        )

        vmware_fcd_write_cache_spec.additional_properties = d
        return vmware_fcd_write_cache_spec

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
