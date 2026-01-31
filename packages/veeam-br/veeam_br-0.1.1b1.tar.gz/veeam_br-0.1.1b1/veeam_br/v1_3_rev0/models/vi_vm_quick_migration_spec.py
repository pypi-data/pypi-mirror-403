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


T = TypeVar("T", bound="ViVMQuickMigrationSpec")


@_attrs_define
class ViVMQuickMigrationSpec:
    """Migration settings.

    Attributes:
        destination_host (Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel',
            'VmwareObjectModel']): Inventory object properties.
        resource_pool (Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel', 'VmwareObjectModel',
            Unset]): Inventory object properties.
        folder (Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel', 'VmwareObjectModel', Unset]):
            Inventory object properties.
        datastore (Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel', 'VmwareObjectModel',
            Unset]): Inventory object properties.
        source_proxy_ids (Union[Unset, list[UUID]]): Array of source backup proxies.
        target_proxy_ids (Union[Unset, list[UUID]]): Array of target backup proxies.
        veeam_qm_enabled (Union[Unset, bool]): If `true`, the Veeam Quick Migration mechanism is used. Otherwise, Veeam
            Backup & Replication will use VMware vMotion for migration.
        delete_source_vms_files (Union[Unset, bool]): If `true`, Veeam Backup & Replication will delete source VM files
            upon successful migration.
    """

    destination_host: Union["AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel"]
    resource_pool: Union[
        "AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel", Unset
    ] = UNSET
    folder: Union["AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel", Unset] = (
        UNSET
    )
    datastore: Union[
        "AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel", Unset
    ] = UNSET
    source_proxy_ids: Union[Unset, list[UUID]] = UNSET
    target_proxy_ids: Union[Unset, list[UUID]] = UNSET
    veeam_qm_enabled: Union[Unset, bool] = UNSET
    delete_source_vms_files: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        destination_host: dict[str, Any]
        if isinstance(self.destination_host, VmwareObjectModel):
            destination_host = self.destination_host.to_dict()
        elif isinstance(self.destination_host, CloudDirectorObjectModel):
            destination_host = self.destination_host.to_dict()
        elif isinstance(self.destination_host, HyperVObjectModel):
            destination_host = self.destination_host.to_dict()
        else:
            destination_host = self.destination_host.to_dict()

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

        datastore: Union[Unset, dict[str, Any]]
        if isinstance(self.datastore, Unset):
            datastore = UNSET
        elif isinstance(self.datastore, VmwareObjectModel):
            datastore = self.datastore.to_dict()
        elif isinstance(self.datastore, CloudDirectorObjectModel):
            datastore = self.datastore.to_dict()
        elif isinstance(self.datastore, HyperVObjectModel):
            datastore = self.datastore.to_dict()
        else:
            datastore = self.datastore.to_dict()

        source_proxy_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.source_proxy_ids, Unset):
            source_proxy_ids = []
            for source_proxy_ids_item_data in self.source_proxy_ids:
                source_proxy_ids_item = str(source_proxy_ids_item_data)
                source_proxy_ids.append(source_proxy_ids_item)

        target_proxy_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.target_proxy_ids, Unset):
            target_proxy_ids = []
            for target_proxy_ids_item_data in self.target_proxy_ids:
                target_proxy_ids_item = str(target_proxy_ids_item_data)
                target_proxy_ids.append(target_proxy_ids_item)

        veeam_qm_enabled = self.veeam_qm_enabled

        delete_source_vms_files = self.delete_source_vms_files

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "destinationHost": destination_host,
            }
        )
        if resource_pool is not UNSET:
            field_dict["resourcePool"] = resource_pool
        if folder is not UNSET:
            field_dict["folder"] = folder
        if datastore is not UNSET:
            field_dict["datastore"] = datastore
        if source_proxy_ids is not UNSET:
            field_dict["sourceProxyIds"] = source_proxy_ids
        if target_proxy_ids is not UNSET:
            field_dict["targetProxyIds"] = target_proxy_ids
        if veeam_qm_enabled is not UNSET:
            field_dict["VeeamQMEnabled"] = veeam_qm_enabled
        if delete_source_vms_files is not UNSET:
            field_dict["DeleteSourceVmsFiles"] = delete_source_vms_files

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_object_model import AgentObjectModel
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)

        def _parse_destination_host(
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

        destination_host = _parse_destination_host(d.pop("destinationHost"))

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

        def _parse_datastore(
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

        datastore = _parse_datastore(d.pop("datastore", UNSET))

        source_proxy_ids = []
        _source_proxy_ids = d.pop("sourceProxyIds", UNSET)
        for source_proxy_ids_item_data in _source_proxy_ids or []:
            source_proxy_ids_item = UUID(source_proxy_ids_item_data)

            source_proxy_ids.append(source_proxy_ids_item)

        target_proxy_ids = []
        _target_proxy_ids = d.pop("targetProxyIds", UNSET)
        for target_proxy_ids_item_data in _target_proxy_ids or []:
            target_proxy_ids_item = UUID(target_proxy_ids_item_data)

            target_proxy_ids.append(target_proxy_ids_item)

        veeam_qm_enabled = d.pop("VeeamQMEnabled", UNSET)

        delete_source_vms_files = d.pop("DeleteSourceVmsFiles", UNSET)

        vi_vm_quick_migration_spec = cls(
            destination_host=destination_host,
            resource_pool=resource_pool,
            folder=folder,
            datastore=datastore,
            source_proxy_ids=source_proxy_ids,
            target_proxy_ids=target_proxy_ids,
            veeam_qm_enabled=veeam_qm_enabled,
            delete_source_vms_files=delete_source_vms_files,
        )

        vi_vm_quick_migration_spec.additional_properties = d
        return vi_vm_quick_migration_spec

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
