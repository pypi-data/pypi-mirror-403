from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_backup_item_version_retention_type import EBackupItemVersionRetentionType
from ..types import UNSET, Unset

T = TypeVar("T", bound="BackupItemVersionsSettingsModel")


@_attrs_define
class BackupItemVersionsSettingsModel:
    """Settings for version-based retention policy.

    Attributes:
        version_retention_type (Union[Unset, EBackupItemVersionRetentionType]): Repositories to which the version-based
            retention policy will apply.
        active_version_retention (Union[Unset, int]): Number of file versions that Veeam Backup & Replication will keep
            for active (not deleted) files.
        deleted_version_retention (Union[Unset, int]): Number of file versions that Veeam Backup & Replication will keep
            for deleted files.
    """

    version_retention_type: Union[Unset, EBackupItemVersionRetentionType] = UNSET
    active_version_retention: Union[Unset, int] = UNSET
    deleted_version_retention: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        version_retention_type: Union[Unset, str] = UNSET
        if not isinstance(self.version_retention_type, Unset):
            version_retention_type = self.version_retention_type.value

        active_version_retention = self.active_version_retention

        deleted_version_retention = self.deleted_version_retention

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if version_retention_type is not UNSET:
            field_dict["versionRetentionType"] = version_retention_type
        if active_version_retention is not UNSET:
            field_dict["activeVersionRetention"] = active_version_retention
        if deleted_version_retention is not UNSET:
            field_dict["deletedVersionRetention"] = deleted_version_retention

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _version_retention_type = d.pop("versionRetentionType", UNSET)
        version_retention_type: Union[Unset, EBackupItemVersionRetentionType]
        if isinstance(_version_retention_type, Unset):
            version_retention_type = UNSET
        else:
            version_retention_type = EBackupItemVersionRetentionType(_version_retention_type)

        active_version_retention = d.pop("activeVersionRetention", UNSET)

        deleted_version_retention = d.pop("deletedVersionRetention", UNSET)

        backup_item_versions_settings_model = cls(
            version_retention_type=version_retention_type,
            active_version_retention=active_version_retention,
            deleted_version_retention=deleted_version_retention,
        )

        backup_item_versions_settings_model.additional_properties = d
        return backup_item_versions_settings_model

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
