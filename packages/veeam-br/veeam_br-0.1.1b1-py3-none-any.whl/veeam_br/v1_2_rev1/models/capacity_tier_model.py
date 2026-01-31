from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_storage_settings_encryption_model import BackupStorageSettingsEncryptionModel
    from ..models.backup_window_setting_model import BackupWindowSettingModel
    from ..models.capacity_extent_model import CapacityExtentModel
    from ..models.capacity_tier_override_policy_model import CapacityTierOverridePolicyModel


T = TypeVar("T", bound="CapacityTierModel")


@_attrs_define
class CapacityTierModel:
    """Capacity tier.

    Attributes:
        is_enabled (bool): If `true`, the capacity tier is enabled.
        extents (Union[Unset, list['CapacityExtentModel']]): Array of capacity extents.
        offload_window (Union[Unset, BackupWindowSettingModel]): Time scheme that defines permitted days and hours for
            the job to start.
        copy_policy_enabled (Union[Unset, bool]): If `true`, Veeam Backup & Replication copies backups from the
            performance extents to the capacity extent as soon as the backups are created.
        move_policy_enabled (Union[Unset, bool]): If `true`, Veeam Backup & Replication moves backup files that belong
            to inactive backup chains from the performance extents to the capacity extent.
        operational_restore_period_days (Union[Unset, int]): Number of days after which inactive backup chains on the
            performance extents are moved to the capacity extent. Specify *0* to offload inactive backup chains on the same
            day they are created.
        override_policy (Union[Unset, CapacityTierOverridePolicyModel]): Policy that overrides the move policy if the
            scale-out backup repository is reaching its capacity.
        encryption (Union[Unset, BackupStorageSettingsEncryptionModel]): Encryption of backup files.
    """

    is_enabled: bool
    extents: Union[Unset, list["CapacityExtentModel"]] = UNSET
    offload_window: Union[Unset, "BackupWindowSettingModel"] = UNSET
    copy_policy_enabled: Union[Unset, bool] = UNSET
    move_policy_enabled: Union[Unset, bool] = UNSET
    operational_restore_period_days: Union[Unset, int] = UNSET
    override_policy: Union[Unset, "CapacityTierOverridePolicyModel"] = UNSET
    encryption: Union[Unset, "BackupStorageSettingsEncryptionModel"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        extents: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.extents, Unset):
            extents = []
            for extents_item_data in self.extents:
                extents_item = extents_item_data.to_dict()
                extents.append(extents_item)

        offload_window: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.offload_window, Unset):
            offload_window = self.offload_window.to_dict()

        copy_policy_enabled = self.copy_policy_enabled

        move_policy_enabled = self.move_policy_enabled

        operational_restore_period_days = self.operational_restore_period_days

        override_policy: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.override_policy, Unset):
            override_policy = self.override_policy.to_dict()

        encryption: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.encryption, Unset):
            encryption = self.encryption.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if extents is not UNSET:
            field_dict["extents"] = extents
        if offload_window is not UNSET:
            field_dict["offloadWindow"] = offload_window
        if copy_policy_enabled is not UNSET:
            field_dict["copyPolicyEnabled"] = copy_policy_enabled
        if move_policy_enabled is not UNSET:
            field_dict["movePolicyEnabled"] = move_policy_enabled
        if operational_restore_period_days is not UNSET:
            field_dict["operationalRestorePeriodDays"] = operational_restore_period_days
        if override_policy is not UNSET:
            field_dict["overridePolicy"] = override_policy
        if encryption is not UNSET:
            field_dict["encryption"] = encryption

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_storage_settings_encryption_model import BackupStorageSettingsEncryptionModel
        from ..models.backup_window_setting_model import BackupWindowSettingModel
        from ..models.capacity_extent_model import CapacityExtentModel
        from ..models.capacity_tier_override_policy_model import CapacityTierOverridePolicyModel

        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        extents = []
        _extents = d.pop("extents", UNSET)
        for extents_item_data in _extents or []:
            extents_item = CapacityExtentModel.from_dict(extents_item_data)

            extents.append(extents_item)

        _offload_window = d.pop("offloadWindow", UNSET)
        offload_window: Union[Unset, BackupWindowSettingModel]
        if isinstance(_offload_window, Unset):
            offload_window = UNSET
        else:
            offload_window = BackupWindowSettingModel.from_dict(_offload_window)

        copy_policy_enabled = d.pop("copyPolicyEnabled", UNSET)

        move_policy_enabled = d.pop("movePolicyEnabled", UNSET)

        operational_restore_period_days = d.pop("operationalRestorePeriodDays", UNSET)

        _override_policy = d.pop("overridePolicy", UNSET)
        override_policy: Union[Unset, CapacityTierOverridePolicyModel]
        if isinstance(_override_policy, Unset):
            override_policy = UNSET
        else:
            override_policy = CapacityTierOverridePolicyModel.from_dict(_override_policy)

        _encryption = d.pop("encryption", UNSET)
        encryption: Union[Unset, BackupStorageSettingsEncryptionModel]
        if isinstance(_encryption, Unset):
            encryption = UNSET
        else:
            encryption = BackupStorageSettingsEncryptionModel.from_dict(_encryption)

        capacity_tier_model = cls(
            is_enabled=is_enabled,
            extents=extents,
            offload_window=offload_window,
            copy_policy_enabled=copy_policy_enabled,
            move_policy_enabled=move_policy_enabled,
            operational_restore_period_days=operational_restore_period_days,
            override_policy=override_policy,
            encryption=encryption,
        )

        capacity_tier_model.additional_properties = d
        return capacity_tier_model

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
