from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_job_exclusions_spec import BackupJobExclusionsSpec
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="BackupJobVirtualMachinesSpec")


@_attrs_define
class BackupJobVirtualMachinesSpec:
    """Included and excluded objects.

    Attributes:
        includes (list[Union['CloudDirectorObjectModel', 'VmwareObjectModel']]): Array of VMs and VM containers
            processed by the job.
        excludes (Union[Unset, BackupJobExclusionsSpec]): Objects excluded from the job.
    """

    includes: list[Union["CloudDirectorObjectModel", "VmwareObjectModel"]]
    excludes: Union[Unset, "BackupJobExclusionsSpec"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.vmware_object_model import VmwareObjectModel

        includes = []
        for includes_item_data in self.includes:
            includes_item: dict[str, Any]
            if isinstance(includes_item_data, VmwareObjectModel):
                includes_item = includes_item_data.to_dict()
            else:
                includes_item = includes_item_data.to_dict()

            includes.append(includes_item)

        excludes: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.excludes, Unset):
            excludes = self.excludes.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "includes": includes,
            }
        )
        if excludes is not UNSET:
            field_dict["excludes"] = excludes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_job_exclusions_spec import BackupJobExclusionsSpec
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)
        includes = []
        _includes = d.pop("includes")
        for includes_item_data in _includes:

            def _parse_includes_item(data: object) -> Union["CloudDirectorObjectModel", "VmwareObjectModel"]:
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

            includes_item = _parse_includes_item(includes_item_data)

            includes.append(includes_item)

        _excludes = d.pop("excludes", UNSET)
        excludes: Union[Unset, BackupJobExclusionsSpec]
        if isinstance(_excludes, Unset):
            excludes = UNSET
        else:
            excludes = BackupJobExclusionsSpec.from_dict(_excludes)

        backup_job_virtual_machines_spec = cls(
            includes=includes,
            excludes=excludes,
        )

        backup_job_virtual_machines_spec.additional_properties = d
        return backup_job_virtual_machines_spec

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
