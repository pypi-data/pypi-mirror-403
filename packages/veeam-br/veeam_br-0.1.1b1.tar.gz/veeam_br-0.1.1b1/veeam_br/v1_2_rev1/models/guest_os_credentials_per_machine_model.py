from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="GuestOsCredentialsPerMachineModel")


@_attrs_define
class GuestOsCredentialsPerMachineModel:
    """
    Attributes:
        vm_object (Union['CloudDirectorObjectModel', 'VmwareObjectModel']): Inventory object properties.
        windows_creds_id (Union[Unset, UUID]): Credentials ID for a Microsoft Windows VM.
        linux_creds_id (Union[Unset, UUID]): Credentials ID for a Linux VM.
    """

    vm_object: Union["CloudDirectorObjectModel", "VmwareObjectModel"]
    windows_creds_id: Union[Unset, UUID] = UNSET
    linux_creds_id: Union[Unset, UUID] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.vmware_object_model import VmwareObjectModel

        vm_object: dict[str, Any]
        if isinstance(self.vm_object, VmwareObjectModel):
            vm_object = self.vm_object.to_dict()
        else:
            vm_object = self.vm_object.to_dict()

        windows_creds_id: Union[Unset, str] = UNSET
        if not isinstance(self.windows_creds_id, Unset):
            windows_creds_id = str(self.windows_creds_id)

        linux_creds_id: Union[Unset, str] = UNSET
        if not isinstance(self.linux_creds_id, Unset):
            linux_creds_id = str(self.linux_creds_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "vmObject": vm_object,
            }
        )
        if windows_creds_id is not UNSET:
            field_dict["windowsCredsId"] = windows_creds_id
        if linux_creds_id is not UNSET:
            field_dict["linuxCredsId"] = linux_creds_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)

        def _parse_vm_object(data: object) -> Union["CloudDirectorObjectModel", "VmwareObjectModel"]:
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

        vm_object = _parse_vm_object(d.pop("vmObject"))

        _windows_creds_id = d.pop("windowsCredsId", UNSET)
        windows_creds_id: Union[Unset, UUID]
        if isinstance(_windows_creds_id, Unset):
            windows_creds_id = UNSET
        else:
            windows_creds_id = UUID(_windows_creds_id)

        _linux_creds_id = d.pop("linuxCredsId", UNSET)
        linux_creds_id: Union[Unset, UUID]
        if isinstance(_linux_creds_id, Unset):
            linux_creds_id = UNSET
        else:
            linux_creds_id = UUID(_linux_creds_id)

        guest_os_credentials_per_machine_model = cls(
            vm_object=vm_object,
            windows_creds_id=windows_creds_id,
            linux_creds_id=linux_creds_id,
        )

        guest_os_credentials_per_machine_model.additional_properties = d
        return guest_os_credentials_per_machine_model

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
