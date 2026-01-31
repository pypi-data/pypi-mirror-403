from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.guest_os_credentials_per_machine_model import GuestOsCredentialsPerMachineModel
    from ..models.specified_guest_os_credentials_model import SpecifiedGuestOsCredentialsModel


T = TypeVar("T", bound="GuestOsCredentialsModel")


@_attrs_define
class GuestOsCredentialsModel:
    """Custom credentials.

    Attributes:
        use_agent_management_credentials (bool): If `true`, the backup job will use the credentials specified in the
            protection group.
        credentials (Union[Unset, SpecifiedGuestOsCredentialsModel]): Custom credentials.
        credentials_per_machine (Union[Unset, list['GuestOsCredentialsPerMachineModel']]): Array of per-machine
            credentials.
    """

    use_agent_management_credentials: bool
    credentials: Union[Unset, "SpecifiedGuestOsCredentialsModel"] = UNSET
    credentials_per_machine: Union[Unset, list["GuestOsCredentialsPerMachineModel"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        use_agent_management_credentials = self.use_agent_management_credentials

        credentials: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.credentials, Unset):
            credentials = self.credentials.to_dict()

        credentials_per_machine: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.credentials_per_machine, Unset):
            credentials_per_machine = []
            for credentials_per_machine_item_data in self.credentials_per_machine:
                credentials_per_machine_item = credentials_per_machine_item_data.to_dict()
                credentials_per_machine.append(credentials_per_machine_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "useAgentManagementCredentials": use_agent_management_credentials,
            }
        )
        if credentials is not UNSET:
            field_dict["credentials"] = credentials
        if credentials_per_machine is not UNSET:
            field_dict["credentialsPerMachine"] = credentials_per_machine

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.guest_os_credentials_per_machine_model import GuestOsCredentialsPerMachineModel
        from ..models.specified_guest_os_credentials_model import SpecifiedGuestOsCredentialsModel

        d = dict(src_dict)
        use_agent_management_credentials = d.pop("useAgentManagementCredentials")

        _credentials = d.pop("credentials", UNSET)
        credentials: Union[Unset, SpecifiedGuestOsCredentialsModel]
        if isinstance(_credentials, Unset):
            credentials = UNSET
        else:
            credentials = SpecifiedGuestOsCredentialsModel.from_dict(_credentials)

        credentials_per_machine = []
        _credentials_per_machine = d.pop("credentialsPerMachine", UNSET)
        for credentials_per_machine_item_data in _credentials_per_machine or []:
            credentials_per_machine_item = GuestOsCredentialsPerMachineModel.from_dict(
                credentials_per_machine_item_data
            )

            credentials_per_machine.append(credentials_per_machine_item)

        guest_os_credentials_model = cls(
            use_agent_management_credentials=use_agent_management_credentials,
            credentials=credentials,
            credentials_per_machine=credentials_per_machine,
        )

        guest_os_credentials_model.additional_properties = d
        return guest_os_credentials_model

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
