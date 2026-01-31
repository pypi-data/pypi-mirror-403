from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.credentials_import_model import CredentialsImportModel
    from ..models.guest_os_credentials_per_machine_import_model import GuestOsCredentialsPerMachineImportModel


T = TypeVar("T", bound="GuestOsCredentialsImportModel")


@_attrs_define
class GuestOsCredentialsImportModel:
    """VM custom credentials.

    Attributes:
        creds (Union[Unset, CredentialsImportModel]): Credentials used for connection.
        credentials_per_machine (Union[Unset, list['GuestOsCredentialsPerMachineImportModel']]): Array of per-machine
            credentials.
    """

    creds: Union[Unset, "CredentialsImportModel"] = UNSET
    credentials_per_machine: Union[Unset, list["GuestOsCredentialsPerMachineImportModel"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        creds: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.creds, Unset):
            creds = self.creds.to_dict()

        credentials_per_machine: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.credentials_per_machine, Unset):
            credentials_per_machine = []
            for credentials_per_machine_item_data in self.credentials_per_machine:
                credentials_per_machine_item = credentials_per_machine_item_data.to_dict()
                credentials_per_machine.append(credentials_per_machine_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if creds is not UNSET:
            field_dict["creds"] = creds
        if credentials_per_machine is not UNSET:
            field_dict["credentialsPerMachine"] = credentials_per_machine

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.credentials_import_model import CredentialsImportModel
        from ..models.guest_os_credentials_per_machine_import_model import GuestOsCredentialsPerMachineImportModel

        d = dict(src_dict)
        _creds = d.pop("creds", UNSET)
        creds: Union[Unset, CredentialsImportModel]
        if isinstance(_creds, Unset):
            creds = UNSET
        else:
            creds = CredentialsImportModel.from_dict(_creds)

        credentials_per_machine = []
        _credentials_per_machine = d.pop("credentialsPerMachine", UNSET)
        for credentials_per_machine_item_data in _credentials_per_machine or []:
            credentials_per_machine_item = GuestOsCredentialsPerMachineImportModel.from_dict(
                credentials_per_machine_item_data
            )

            credentials_per_machine.append(credentials_per_machine_item)

        guest_os_credentials_import_model = cls(
            creds=creds,
            credentials_per_machine=credentials_per_machine,
        )

        guest_os_credentials_import_model.additional_properties = d
        return guest_os_credentials_import_model

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
