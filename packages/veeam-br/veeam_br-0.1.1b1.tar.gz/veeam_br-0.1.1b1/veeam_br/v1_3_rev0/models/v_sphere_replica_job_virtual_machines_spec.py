from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_object_model import AgentObjectModel
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.hyper_v_object_model import HyperVObjectModel
    from ..models.replica_source_repositories_model import ReplicaSourceRepositoriesModel
    from ..models.v_sphere_replica_job_exclusions_spec import VSphereReplicaJobExclusionsSpec
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="VSphereReplicaJobVirtualMachinesSpec")


@_attrs_define
class VSphereReplicaJobVirtualMachinesSpec:
    """Included and excluded objects.

    Attributes:
        includes (list[Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel',
            'VmwareObjectModel']]): Array of VMs and VM containers processed by the job.
        excludes (Union[Unset, VSphereReplicaJobExclusionsSpec]): Objects excluded from the job.
        source_repositories (Union[Unset, ReplicaSourceRepositoriesModel]): Source to obtain VM data from.
    """

    includes: list[Union["AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel"]]
    excludes: Union[Unset, "VSphereReplicaJobExclusionsSpec"] = UNSET
    source_repositories: Union[Unset, "ReplicaSourceRepositoriesModel"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        includes = []
        for includes_item_data in self.includes:
            includes_item: dict[str, Any]
            if isinstance(includes_item_data, VmwareObjectModel):
                includes_item = includes_item_data.to_dict()
            elif isinstance(includes_item_data, CloudDirectorObjectModel):
                includes_item = includes_item_data.to_dict()
            elif isinstance(includes_item_data, HyperVObjectModel):
                includes_item = includes_item_data.to_dict()
            else:
                includes_item = includes_item_data.to_dict()

            includes.append(includes_item)

        excludes: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.excludes, Unset):
            excludes = self.excludes.to_dict()

        source_repositories: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.source_repositories, Unset):
            source_repositories = self.source_repositories.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "includes": includes,
            }
        )
        if excludes is not UNSET:
            field_dict["excludes"] = excludes
        if source_repositories is not UNSET:
            field_dict["sourceRepositories"] = source_repositories

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_object_model import AgentObjectModel
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.replica_source_repositories_model import ReplicaSourceRepositoriesModel
        from ..models.v_sphere_replica_job_exclusions_spec import VSphereReplicaJobExclusionsSpec
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)
        includes = []
        _includes = d.pop("includes")
        for includes_item_data in _includes:

            def _parse_includes_item(
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

            includes_item = _parse_includes_item(includes_item_data)

            includes.append(includes_item)

        _excludes = d.pop("excludes", UNSET)
        excludes: Union[Unset, VSphereReplicaJobExclusionsSpec]
        if isinstance(_excludes, Unset):
            excludes = UNSET
        else:
            excludes = VSphereReplicaJobExclusionsSpec.from_dict(_excludes)

        _source_repositories = d.pop("sourceRepositories", UNSET)
        source_repositories: Union[Unset, ReplicaSourceRepositoriesModel]
        if isinstance(_source_repositories, Unset):
            source_repositories = UNSET
        else:
            source_repositories = ReplicaSourceRepositoriesModel.from_dict(_source_repositories)

        v_sphere_replica_job_virtual_machines_spec = cls(
            includes=includes,
            excludes=excludes,
            source_repositories=source_repositories,
        )

        v_sphere_replica_job_virtual_machines_spec.additional_properties = d
        return v_sphere_replica_job_virtual_machines_spec

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
