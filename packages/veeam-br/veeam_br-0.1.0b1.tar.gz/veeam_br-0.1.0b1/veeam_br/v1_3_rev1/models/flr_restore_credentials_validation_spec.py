from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_flr_restore_mode_type import EFlrRestoreModeType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_flr_restore_target_host_model import AgentFlrRestoreTargetHostModel
    from ..models.cloud_director_flr_restore_target_host_model import CloudDirectorFlrRestoreTargetHostModel
    from ..models.hyper_v_flr_restore_target_host_model import HyperVFlrRestoreTargetHostModel
    from ..models.vmware_flr_restore_target_host_model import VmwareFlrRestoreTargetHostModel


T = TypeVar("T", bound="FlrRestoreCredentialsValidationSpec")


@_attrs_define
class FlrRestoreCredentialsValidationSpec:
    """Settings for credentials validation for the target machine for the file-level restore.

    Attributes:
        restore_mode (EFlrRestoreModeType): Restore mode for file-level restore.
        credentials_id (Union[Unset, UUID]): ID of a credentials record used to connect to the target machine. If the ID
            is not specified, Veeam Backup & Replication will try to find credentials for the target machine in the stored
            credential records.
        target_host (Union['AgentFlrRestoreTargetHostModel', 'CloudDirectorFlrRestoreTargetHostModel',
            'HyperVFlrRestoreTargetHostModel', 'VmwareFlrRestoreTargetHostModel', Unset]): Target machine. To get an
            inventory object, run the [Get Inventory Objects](Inventory-Browser#operation/GetInventoryObjects) request.
    """

    restore_mode: EFlrRestoreModeType
    credentials_id: Union[Unset, UUID] = UNSET
    target_host: Union[
        "AgentFlrRestoreTargetHostModel",
        "CloudDirectorFlrRestoreTargetHostModel",
        "HyperVFlrRestoreTargetHostModel",
        "VmwareFlrRestoreTargetHostModel",
        Unset,
    ] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.agent_flr_restore_target_host_model import AgentFlrRestoreTargetHostModel
        from ..models.hyper_v_flr_restore_target_host_model import HyperVFlrRestoreTargetHostModel
        from ..models.vmware_flr_restore_target_host_model import VmwareFlrRestoreTargetHostModel

        restore_mode = self.restore_mode.value

        credentials_id: Union[Unset, str] = UNSET
        if not isinstance(self.credentials_id, Unset):
            credentials_id = str(self.credentials_id)

        target_host: Union[Unset, dict[str, Any]]
        if isinstance(self.target_host, Unset):
            target_host = UNSET
        elif isinstance(self.target_host, VmwareFlrRestoreTargetHostModel):
            target_host = self.target_host.to_dict()
        elif isinstance(self.target_host, HyperVFlrRestoreTargetHostModel):
            target_host = self.target_host.to_dict()
        elif isinstance(self.target_host, AgentFlrRestoreTargetHostModel):
            target_host = self.target_host.to_dict()
        else:
            target_host = self.target_host.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "restoreMode": restore_mode,
            }
        )
        if credentials_id is not UNSET:
            field_dict["credentialsId"] = credentials_id
        if target_host is not UNSET:
            field_dict["targetHost"] = target_host

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_flr_restore_target_host_model import AgentFlrRestoreTargetHostModel
        from ..models.cloud_director_flr_restore_target_host_model import CloudDirectorFlrRestoreTargetHostModel
        from ..models.hyper_v_flr_restore_target_host_model import HyperVFlrRestoreTargetHostModel
        from ..models.vmware_flr_restore_target_host_model import VmwareFlrRestoreTargetHostModel

        d = dict(src_dict)
        restore_mode = EFlrRestoreModeType(d.pop("restoreMode"))

        _credentials_id = d.pop("credentialsId", UNSET)
        credentials_id: Union[Unset, UUID]
        if isinstance(_credentials_id, Unset):
            credentials_id = UNSET
        else:
            credentials_id = UUID(_credentials_id)

        def _parse_target_host(
            data: object,
        ) -> Union[
            "AgentFlrRestoreTargetHostModel",
            "CloudDirectorFlrRestoreTargetHostModel",
            "HyperVFlrRestoreTargetHostModel",
            "VmwareFlrRestoreTargetHostModel",
            Unset,
        ]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_flr_restore_target_host_model_type_0 = VmwareFlrRestoreTargetHostModel.from_dict(data)

                return componentsschemas_flr_restore_target_host_model_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_flr_restore_target_host_model_type_1 = HyperVFlrRestoreTargetHostModel.from_dict(data)

                return componentsschemas_flr_restore_target_host_model_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_flr_restore_target_host_model_type_2 = AgentFlrRestoreTargetHostModel.from_dict(data)

                return componentsschemas_flr_restore_target_host_model_type_2
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_flr_restore_target_host_model_type_3 = CloudDirectorFlrRestoreTargetHostModel.from_dict(
                data
            )

            return componentsschemas_flr_restore_target_host_model_type_3

        target_host = _parse_target_host(d.pop("targetHost", UNSET))

        flr_restore_credentials_validation_spec = cls(
            restore_mode=restore_mode,
            credentials_id=credentials_id,
            target_host=target_host,
        )

        flr_restore_credentials_validation_spec.additional_properties = d
        return flr_restore_credentials_validation_spec

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
