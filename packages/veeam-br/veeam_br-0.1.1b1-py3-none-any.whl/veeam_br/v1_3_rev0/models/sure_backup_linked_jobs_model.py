from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_object_model import AgentObjectModel
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.hyper_v_object_model import HyperVObjectModel
    from ..models.job_object_model import JobObjectModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="SureBackupLinkedJobsModel")


@_attrs_define
class SureBackupLinkedJobsModel:
    """Backup or replication jobs with machines that you want to verify with the SureBackup job.

    Attributes:
        includes (list['JobObjectModel']): Array of backup or replication jobs.
        excludes (Union[Unset, list[Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel',
            'VmwareObjectModel']]]): Array of objects that the SureBackup job will exclude from processing.
        max_concurrent_machines_count (Union[Unset, int]): Maximum number of machines (from a linked job) that can be
            processed at the same time.
        process_random_machines (Union[Unset, bool]): If `true`, a number of random machines will be randomly tested.
        max_random_machines_count (Union[Unset, int]): Maximum number of machines that will be randomly tested.
    """

    includes: list["JobObjectModel"]
    excludes: Union[
        Unset, list[Union["AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel"]]
    ] = UNSET
    max_concurrent_machines_count: Union[Unset, int] = UNSET
    process_random_machines: Union[Unset, bool] = UNSET
    max_random_machines_count: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        includes = []
        for includes_item_data in self.includes:
            includes_item = includes_item_data.to_dict()
            includes.append(includes_item)

        excludes: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.excludes, Unset):
            excludes = []
            for excludes_item_data in self.excludes:
                excludes_item: dict[str, Any]
                if isinstance(excludes_item_data, VmwareObjectModel):
                    excludes_item = excludes_item_data.to_dict()
                elif isinstance(excludes_item_data, CloudDirectorObjectModel):
                    excludes_item = excludes_item_data.to_dict()
                elif isinstance(excludes_item_data, HyperVObjectModel):
                    excludes_item = excludes_item_data.to_dict()
                else:
                    excludes_item = excludes_item_data.to_dict()

                excludes.append(excludes_item)

        max_concurrent_machines_count = self.max_concurrent_machines_count

        process_random_machines = self.process_random_machines

        max_random_machines_count = self.max_random_machines_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "includes": includes,
            }
        )
        if excludes is not UNSET:
            field_dict["excludes"] = excludes
        if max_concurrent_machines_count is not UNSET:
            field_dict["maxConcurrentMachinesCount"] = max_concurrent_machines_count
        if process_random_machines is not UNSET:
            field_dict["processRandomMachines"] = process_random_machines
        if max_random_machines_count is not UNSET:
            field_dict["maxRandomMachinesCount"] = max_random_machines_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_object_model import AgentObjectModel
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.job_object_model import JobObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)
        includes = []
        _includes = d.pop("includes")
        for includes_item_data in _includes:
            includes_item = JobObjectModel.from_dict(includes_item_data)

            includes.append(includes_item)

        excludes = []
        _excludes = d.pop("excludes", UNSET)
        for excludes_item_data in _excludes or []:

            def _parse_excludes_item(
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

            excludes_item = _parse_excludes_item(excludes_item_data)

            excludes.append(excludes_item)

        max_concurrent_machines_count = d.pop("maxConcurrentMachinesCount", UNSET)

        process_random_machines = d.pop("processRandomMachines", UNSET)

        max_random_machines_count = d.pop("maxRandomMachinesCount", UNSET)

        sure_backup_linked_jobs_model = cls(
            includes=includes,
            excludes=excludes,
            max_concurrent_machines_count=max_concurrent_machines_count,
            process_random_machines=process_random_machines,
            max_random_machines_count=max_random_machines_count,
        )

        sure_backup_linked_jobs_model.additional_properties = d
        return sure_backup_linked_jobs_model

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
