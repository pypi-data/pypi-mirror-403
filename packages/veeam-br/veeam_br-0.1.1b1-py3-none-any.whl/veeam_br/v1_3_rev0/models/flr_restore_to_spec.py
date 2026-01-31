from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_flr_restore_type import EFlrRestoreType

if TYPE_CHECKING:
    from ..models.agent_flr_restore_target_host_model import AgentFlrRestoreTargetHostModel
    from ..models.cloud_director_flr_restore_target_host_model import CloudDirectorFlrRestoreTargetHostModel
    from ..models.hyper_v_flr_restore_target_host_model import HyperVFlrRestoreTargetHostModel
    from ..models.vmware_flr_restore_target_host_model import VmwareFlrRestoreTargetHostModel


T = TypeVar("T", bound="FlrRestoreToSpec")


@_attrs_define
class FlrRestoreToSpec:
    """Settings for restoring files and folders to another location.

    Attributes:
        source_path (list[str]): Array of paths to the items that you want to restore.
        restore_type (EFlrRestoreType): Restore type.
        credentials_id (UUID): ID of a credentials record used to connect to the target machine.
        target_host (Union['AgentFlrRestoreTargetHostModel', 'CloudDirectorFlrRestoreTargetHostModel',
            'HyperVFlrRestoreTargetHostModel', 'VmwareFlrRestoreTargetHostModel']): Target machine. To get an invetory
            object, use the [Get Inventory Objects](Inventory-Browser#operation/GetInventoryObjects) request.
        target_path (str): Path to the target folder.
    """

    source_path: list[str]
    restore_type: EFlrRestoreType
    credentials_id: UUID
    target_host: Union[
        "AgentFlrRestoreTargetHostModel",
        "CloudDirectorFlrRestoreTargetHostModel",
        "HyperVFlrRestoreTargetHostModel",
        "VmwareFlrRestoreTargetHostModel",
    ]
    target_path: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.agent_flr_restore_target_host_model import AgentFlrRestoreTargetHostModel
        from ..models.hyper_v_flr_restore_target_host_model import HyperVFlrRestoreTargetHostModel
        from ..models.vmware_flr_restore_target_host_model import VmwareFlrRestoreTargetHostModel

        source_path = self.source_path

        restore_type = self.restore_type.value

        credentials_id = str(self.credentials_id)

        target_host: dict[str, Any]
        if isinstance(self.target_host, VmwareFlrRestoreTargetHostModel):
            target_host = self.target_host.to_dict()
        elif isinstance(self.target_host, HyperVFlrRestoreTargetHostModel):
            target_host = self.target_host.to_dict()
        elif isinstance(self.target_host, AgentFlrRestoreTargetHostModel):
            target_host = self.target_host.to_dict()
        else:
            target_host = self.target_host.to_dict()

        target_path = self.target_path

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sourcePath": source_path,
                "restoreType": restore_type,
                "credentialsId": credentials_id,
                "targetHost": target_host,
                "targetPath": target_path,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_flr_restore_target_host_model import AgentFlrRestoreTargetHostModel
        from ..models.cloud_director_flr_restore_target_host_model import CloudDirectorFlrRestoreTargetHostModel
        from ..models.hyper_v_flr_restore_target_host_model import HyperVFlrRestoreTargetHostModel
        from ..models.vmware_flr_restore_target_host_model import VmwareFlrRestoreTargetHostModel

        d = dict(src_dict)
        source_path = cast(list[str], d.pop("sourcePath"))

        restore_type = EFlrRestoreType(d.pop("restoreType"))

        credentials_id = UUID(d.pop("credentialsId"))

        def _parse_target_host(
            data: object,
        ) -> Union[
            "AgentFlrRestoreTargetHostModel",
            "CloudDirectorFlrRestoreTargetHostModel",
            "HyperVFlrRestoreTargetHostModel",
            "VmwareFlrRestoreTargetHostModel",
        ]:
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

        target_host = _parse_target_host(d.pop("targetHost"))

        target_path = d.pop("targetPath")

        flr_restore_to_spec = cls(
            source_path=source_path,
            restore_type=restore_type,
            credentials_id=credentials_id,
            target_host=target_host,
            target_path=target_path,
        )

        flr_restore_to_spec.additional_properties = d
        return flr_restore_to_spec

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
