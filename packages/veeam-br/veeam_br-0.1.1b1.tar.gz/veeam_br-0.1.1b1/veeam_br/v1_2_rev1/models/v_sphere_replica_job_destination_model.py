from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.v_sphere_replica_job_destination_mapping_model import VSphereReplicaJobDestinationMappingModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="VSphereReplicaJobDestinationModel")


@_attrs_define
class VSphereReplicaJobDestinationModel:
    """Replica destination&#58; target host or cluster, target resource pool, target folder, target datastore and mapping
    rules.

        Attributes:
            host (Union['CloudDirectorObjectModel', 'VmwareObjectModel']): Inventory object properties.
            resource_pool (Union['CloudDirectorObjectModel', 'VmwareObjectModel']): Inventory object properties.
            folder (Union['CloudDirectorObjectModel', 'VmwareObjectModel']): Inventory object properties.
            datastore (Union['CloudDirectorObjectModel', 'VmwareObjectModel']): Inventory object properties.
            mapping_rules (Union[Unset, list['VSphereReplicaJobDestinationMappingModel']]): Mapping rules that define files
                location and disk provisioning types for replica VMs.<ul><li>`vmObject` — VM that you customize files location
                for.</li><li>`configurationFilesDatastoreMapping` — Datastore for replica configuration
                files.</li><li>`diskFilesMapping` — Mapping rules for VM disks.</li></ul>
    """

    host: Union["CloudDirectorObjectModel", "VmwareObjectModel"]
    resource_pool: Union["CloudDirectorObjectModel", "VmwareObjectModel"]
    folder: Union["CloudDirectorObjectModel", "VmwareObjectModel"]
    datastore: Union["CloudDirectorObjectModel", "VmwareObjectModel"]
    mapping_rules: Union[Unset, list["VSphereReplicaJobDestinationMappingModel"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.vmware_object_model import VmwareObjectModel

        host: dict[str, Any]
        if isinstance(self.host, VmwareObjectModel):
            host = self.host.to_dict()
        else:
            host = self.host.to_dict()

        resource_pool: dict[str, Any]
        if isinstance(self.resource_pool, VmwareObjectModel):
            resource_pool = self.resource_pool.to_dict()
        else:
            resource_pool = self.resource_pool.to_dict()

        folder: dict[str, Any]
        if isinstance(self.folder, VmwareObjectModel):
            folder = self.folder.to_dict()
        else:
            folder = self.folder.to_dict()

        datastore: dict[str, Any]
        if isinstance(self.datastore, VmwareObjectModel):
            datastore = self.datastore.to_dict()
        else:
            datastore = self.datastore.to_dict()

        mapping_rules: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.mapping_rules, Unset):
            mapping_rules = []
            for mapping_rules_item_data in self.mapping_rules:
                mapping_rules_item = mapping_rules_item_data.to_dict()
                mapping_rules.append(mapping_rules_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "host": host,
                "resourcePool": resource_pool,
                "folder": folder,
                "datastore": datastore,
            }
        )
        if mapping_rules is not UNSET:
            field_dict["mappingRules"] = mapping_rules

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.v_sphere_replica_job_destination_mapping_model import VSphereReplicaJobDestinationMappingModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)

        def _parse_host(data: object) -> Union["CloudDirectorObjectModel", "VmwareObjectModel"]:
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

        host = _parse_host(d.pop("host"))

        def _parse_resource_pool(data: object) -> Union["CloudDirectorObjectModel", "VmwareObjectModel"]:
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

        resource_pool = _parse_resource_pool(d.pop("resourcePool"))

        def _parse_folder(data: object) -> Union["CloudDirectorObjectModel", "VmwareObjectModel"]:
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

        folder = _parse_folder(d.pop("folder"))

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

        mapping_rules = []
        _mapping_rules = d.pop("mappingRules", UNSET)
        for mapping_rules_item_data in _mapping_rules or []:
            mapping_rules_item = VSphereReplicaJobDestinationMappingModel.from_dict(mapping_rules_item_data)

            mapping_rules.append(mapping_rules_item)

        v_sphere_replica_job_destination_model = cls(
            host=host,
            resource_pool=resource_pool,
            folder=folder,
            datastore=datastore,
            mapping_rules=mapping_rules,
        )

        v_sphere_replica_job_destination_model.additional_properties = d
        return v_sphere_replica_job_destination_model

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
