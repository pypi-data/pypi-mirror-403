from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_object_model import AgentObjectModel
    from ..models.backup_object_indexing_model import BackupObjectIndexingModel
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.hyper_v_object_model import HyperVObjectModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="BackupIndexingSettingsModel")


@_attrs_define
class BackupIndexingSettingsModel:
    """Backup indexing settings.

    Attributes:
        vm_object (Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel', 'VmwareObjectModel']):
            Inventory object properties.
        windows_indexing (Union[Unset, BackupObjectIndexingModel]): Guest OS indexing options for the VM.
        linux_indexing (Union[Unset, BackupObjectIndexingModel]): Guest OS indexing options for the VM.
    """

    vm_object: Union["AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel"]
    windows_indexing: Union[Unset, "BackupObjectIndexingModel"] = UNSET
    linux_indexing: Union[Unset, "BackupObjectIndexingModel"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        vm_object: dict[str, Any]
        if isinstance(self.vm_object, VmwareObjectModel):
            vm_object = self.vm_object.to_dict()
        elif isinstance(self.vm_object, CloudDirectorObjectModel):
            vm_object = self.vm_object.to_dict()
        elif isinstance(self.vm_object, HyperVObjectModel):
            vm_object = self.vm_object.to_dict()
        else:
            vm_object = self.vm_object.to_dict()

        windows_indexing: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.windows_indexing, Unset):
            windows_indexing = self.windows_indexing.to_dict()

        linux_indexing: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.linux_indexing, Unset):
            linux_indexing = self.linux_indexing.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "vmObject": vm_object,
            }
        )
        if windows_indexing is not UNSET:
            field_dict["WindowsIndexing"] = windows_indexing
        if linux_indexing is not UNSET:
            field_dict["LinuxIndexing"] = linux_indexing

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_object_model import AgentObjectModel
        from ..models.backup_object_indexing_model import BackupObjectIndexingModel
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)

        def _parse_vm_object(
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

        vm_object = _parse_vm_object(d.pop("vmObject"))

        _windows_indexing = d.pop("WindowsIndexing", UNSET)
        windows_indexing: Union[Unset, BackupObjectIndexingModel]
        if isinstance(_windows_indexing, Unset):
            windows_indexing = UNSET
        else:
            windows_indexing = BackupObjectIndexingModel.from_dict(_windows_indexing)

        _linux_indexing = d.pop("LinuxIndexing", UNSET)
        linux_indexing: Union[Unset, BackupObjectIndexingModel]
        if isinstance(_linux_indexing, Unset):
            linux_indexing = UNSET
        else:
            linux_indexing = BackupObjectIndexingModel.from_dict(_linux_indexing)

        backup_indexing_settings_model = cls(
            vm_object=vm_object,
            windows_indexing=windows_indexing,
            linux_indexing=linux_indexing,
        )

        backup_indexing_settings_model.additional_properties = d
        return backup_indexing_settings_model

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
