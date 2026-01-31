from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.credentials_import_model import CredentialsImportModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="GuestOsCredentialsPerMachineImportModel")


@_attrs_define
class GuestOsCredentialsPerMachineImportModel:
    """
    Attributes:
        vm_object (Union['CloudDirectorObjectModel', 'VmwareObjectModel']): Inventory object properties.
        windows_creds (Union[Unset, CredentialsImportModel]): Credentials used for connection.
        linux_creds (Union[Unset, CredentialsImportModel]): Credentials used for connection.
    """

    vm_object: Union["CloudDirectorObjectModel", "VmwareObjectModel"]
    windows_creds: Union[Unset, "CredentialsImportModel"] = UNSET
    linux_creds: Union[Unset, "CredentialsImportModel"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.vmware_object_model import VmwareObjectModel

        vm_object: dict[str, Any]
        if isinstance(self.vm_object, VmwareObjectModel):
            vm_object = self.vm_object.to_dict()
        else:
            vm_object = self.vm_object.to_dict()

        windows_creds: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.windows_creds, Unset):
            windows_creds = self.windows_creds.to_dict()

        linux_creds: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.linux_creds, Unset):
            linux_creds = self.linux_creds.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "vmObject": vm_object,
            }
        )
        if windows_creds is not UNSET:
            field_dict["windowsCreds"] = windows_creds
        if linux_creds is not UNSET:
            field_dict["linuxCreds"] = linux_creds

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.credentials_import_model import CredentialsImportModel
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

        _windows_creds = d.pop("windowsCreds", UNSET)
        windows_creds: Union[Unset, CredentialsImportModel]
        if isinstance(_windows_creds, Unset):
            windows_creds = UNSET
        else:
            windows_creds = CredentialsImportModel.from_dict(_windows_creds)

        _linux_creds = d.pop("linuxCreds", UNSET)
        linux_creds: Union[Unset, CredentialsImportModel]
        if isinstance(_linux_creds, Unset):
            linux_creds = UNSET
        else:
            linux_creds = CredentialsImportModel.from_dict(_linux_creds)

        guest_os_credentials_per_machine_import_model = cls(
            vm_object=vm_object,
            windows_creds=windows_creds,
            linux_creds=linux_creds,
        )

        guest_os_credentials_per_machine_import_model.additional_properties = d
        return guest_os_credentials_per_machine_import_model

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
