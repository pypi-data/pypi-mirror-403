from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_instant_recovery_mount_state import EInstantRecoveryMountState
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.vmware_fcd_instant_recovery_disk_info import VmwareFcdInstantRecoveryDiskInfo
    from ..models.vmware_fcd_instant_recovery_spec import VmwareFcdInstantRecoverySpec


T = TypeVar("T", bound="VmwareFcdInstantRecoveryMount")


@_attrs_define
class VmwareFcdInstantRecoveryMount:
    """
    Attributes:
        id (UUID): Mount point ID.
        session_id (UUID): Restore session ID. Use the ID to track the progress. For details, see [Get
            Session](#tag/Sessions/operation/GetSession).
        state (EInstantRecoveryMountState): Mount state.
        spec (VmwareFcdInstantRecoverySpec): Instant FCD Recovery configuration:<ul> <li>Restore point ID</li>
            <li>Destination cluster</li> <li>Disks for restore</li> <li>Write cache</li></ul>
        error_message (Union[Unset, str]): Error message.
        mounted_disks (Union[Unset, list['VmwareFcdInstantRecoveryDiskInfo']]): Array of mounted disks.
    """

    id: UUID
    session_id: UUID
    state: EInstantRecoveryMountState
    spec: "VmwareFcdInstantRecoverySpec"
    error_message: Union[Unset, str] = UNSET
    mounted_disks: Union[Unset, list["VmwareFcdInstantRecoveryDiskInfo"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        session_id = str(self.session_id)

        state = self.state.value

        spec = self.spec.to_dict()

        error_message = self.error_message

        mounted_disks: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.mounted_disks, Unset):
            mounted_disks = []
            for mounted_disks_item_data in self.mounted_disks:
                mounted_disks_item = mounted_disks_item_data.to_dict()
                mounted_disks.append(mounted_disks_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "sessionId": session_id,
                "state": state,
                "spec": spec,
            }
        )
        if error_message is not UNSET:
            field_dict["errorMessage"] = error_message
        if mounted_disks is not UNSET:
            field_dict["mountedDisks"] = mounted_disks

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.vmware_fcd_instant_recovery_disk_info import VmwareFcdInstantRecoveryDiskInfo
        from ..models.vmware_fcd_instant_recovery_spec import VmwareFcdInstantRecoverySpec

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        session_id = UUID(d.pop("sessionId"))

        state = EInstantRecoveryMountState(d.pop("state"))

        spec = VmwareFcdInstantRecoverySpec.from_dict(d.pop("spec"))

        error_message = d.pop("errorMessage", UNSET)

        mounted_disks = []
        _mounted_disks = d.pop("mountedDisks", UNSET)
        for mounted_disks_item_data in _mounted_disks or []:
            mounted_disks_item = VmwareFcdInstantRecoveryDiskInfo.from_dict(mounted_disks_item_data)

            mounted_disks.append(mounted_disks_item)

        vmware_fcd_instant_recovery_mount = cls(
            id=id,
            session_id=session_id,
            state=state,
            spec=spec,
            error_message=error_message,
            mounted_disks=mounted_disks,
        )

        vmware_fcd_instant_recovery_mount.additional_properties = d
        return vmware_fcd_instant_recovery_mount

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
