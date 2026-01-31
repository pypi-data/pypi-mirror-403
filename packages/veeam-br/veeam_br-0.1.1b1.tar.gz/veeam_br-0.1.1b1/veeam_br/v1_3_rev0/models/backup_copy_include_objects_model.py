from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.job_object_model import JobObjectModel
    from ..models.repository_object_model import RepositoryObjectModel


T = TypeVar("T", bound="BackupCopyIncludeObjectsModel")


@_attrs_define
class BackupCopyIncludeObjectsModel:
    """Included objects.

    Attributes:
        jobs (Union[Unset, list['JobObjectModel']]): Array of jobs to be processed by the job.
        repositories (Union[Unset, list['RepositoryObjectModel']]): Array of repositories processed by the job.
    """

    jobs: Union[Unset, list["JobObjectModel"]] = UNSET
    repositories: Union[Unset, list["RepositoryObjectModel"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        jobs: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.jobs, Unset):
            jobs = []
            for jobs_item_data in self.jobs:
                jobs_item = jobs_item_data.to_dict()
                jobs.append(jobs_item)

        repositories: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.repositories, Unset):
            repositories = []
            for repositories_item_data in self.repositories:
                repositories_item = repositories_item_data.to_dict()
                repositories.append(repositories_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if jobs is not UNSET:
            field_dict["jobs"] = jobs
        if repositories is not UNSET:
            field_dict["repositories"] = repositories

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.job_object_model import JobObjectModel
        from ..models.repository_object_model import RepositoryObjectModel

        d = dict(src_dict)
        jobs = []
        _jobs = d.pop("jobs", UNSET)
        for jobs_item_data in _jobs or []:
            jobs_item = JobObjectModel.from_dict(jobs_item_data)

            jobs.append(jobs_item)

        repositories = []
        _repositories = d.pop("repositories", UNSET)
        for repositories_item_data in _repositories or []:
            repositories_item = RepositoryObjectModel.from_dict(repositories_item_data)

            repositories.append(repositories_item)

        backup_copy_include_objects_model = cls(
            jobs=jobs,
            repositories=repositories,
        )

        backup_copy_include_objects_model.additional_properties = d
        return backup_copy_include_objects_model

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
