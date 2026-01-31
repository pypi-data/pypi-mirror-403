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


T = TypeVar("T", bound="BackupCopyExcludeObjectsModel")


@_attrs_define
class BackupCopyExcludeObjectsModel:
    """Excluded objects.

    Attributes:
        jobs (Union[Unset, list['JobObjectModel']]): Array of jobs, excluded from the job.
        objects (Union[Unset, list[Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel',
            'VmwareObjectModel']]]): Array of objects, excluded from the job.
    """

    jobs: Union[Unset, list["JobObjectModel"]] = UNSET
    objects: Union[
        Unset, list[Union["AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel"]]
    ] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        jobs: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.jobs, Unset):
            jobs = []
            for jobs_item_data in self.jobs:
                jobs_item = jobs_item_data.to_dict()
                jobs.append(jobs_item)

        objects: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.objects, Unset):
            objects = []
            for objects_item_data in self.objects:
                objects_item: dict[str, Any]
                if isinstance(objects_item_data, VmwareObjectModel):
                    objects_item = objects_item_data.to_dict()
                elif isinstance(objects_item_data, CloudDirectorObjectModel):
                    objects_item = objects_item_data.to_dict()
                elif isinstance(objects_item_data, HyperVObjectModel):
                    objects_item = objects_item_data.to_dict()
                else:
                    objects_item = objects_item_data.to_dict()

                objects.append(objects_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if jobs is not UNSET:
            field_dict["jobs"] = jobs
        if objects is not UNSET:
            field_dict["objects"] = objects

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_object_model import AgentObjectModel
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.job_object_model import JobObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)
        jobs = []
        _jobs = d.pop("jobs", UNSET)
        for jobs_item_data in _jobs or []:
            jobs_item = JobObjectModel.from_dict(jobs_item_data)

            jobs.append(jobs_item)

        objects = []
        _objects = d.pop("objects", UNSET)
        for objects_item_data in _objects or []:

            def _parse_objects_item(
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

            objects_item = _parse_objects_item(objects_item_data)

            objects.append(objects_item)

        backup_copy_exclude_objects_model = cls(
            jobs=jobs,
            objects=objects,
        )

        backup_copy_exclude_objects_model.additional_properties = d
        return backup_copy_exclude_objects_model

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
