from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_health_check_settings_models import BackupHealthCheckSettingsModels
    from ..models.backup_item_versions_settings_model import BackupItemVersionsSettingsModel
    from ..models.file_backup_notification_settings_model import FileBackupNotificationSettingsModel
    from ..models.file_backup_storage_settings_model import FileBackupStorageSettingsModel
    from ..models.job_scripts_settings_model import JobScriptsSettingsModel


T = TypeVar("T", bound="ObjectStorageBackupJobAdvancedSettingsModel")


@_attrs_define
class ObjectStorageBackupJobAdvancedSettingsModel:
    """Advanced settings for object storage backup job.

    Attributes:
        object_versions (Union[Unset, BackupItemVersionsSettingsModel]): Settings for version-based retention policy.
        storage_data (Union[Unset, FileBackupStorageSettingsModel]): Storage settings for file backup.
        backup_health (Union[Unset, BackupHealthCheckSettingsModels]): Health check settings for the latest restore
            point in the backup chain.
        scripts (Union[Unset, JobScriptsSettingsModel]): Script settings.<ul><li>`preCommand` — script executed before
            the job</li><li>`postCommand` — script executed after the job</li></ul>
        notifications (Union[Unset, FileBackupNotificationSettingsModel]): Notification settings for file backup.
    """

    object_versions: Union[Unset, "BackupItemVersionsSettingsModel"] = UNSET
    storage_data: Union[Unset, "FileBackupStorageSettingsModel"] = UNSET
    backup_health: Union[Unset, "BackupHealthCheckSettingsModels"] = UNSET
    scripts: Union[Unset, "JobScriptsSettingsModel"] = UNSET
    notifications: Union[Unset, "FileBackupNotificationSettingsModel"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        object_versions: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.object_versions, Unset):
            object_versions = self.object_versions.to_dict()

        storage_data: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.storage_data, Unset):
            storage_data = self.storage_data.to_dict()

        backup_health: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.backup_health, Unset):
            backup_health = self.backup_health.to_dict()

        scripts: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.scripts, Unset):
            scripts = self.scripts.to_dict()

        notifications: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.notifications, Unset):
            notifications = self.notifications.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if object_versions is not UNSET:
            field_dict["objectVersions"] = object_versions
        if storage_data is not UNSET:
            field_dict["storageData"] = storage_data
        if backup_health is not UNSET:
            field_dict["backupHealth"] = backup_health
        if scripts is not UNSET:
            field_dict["scripts"] = scripts
        if notifications is not UNSET:
            field_dict["notifications"] = notifications

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_health_check_settings_models import BackupHealthCheckSettingsModels
        from ..models.backup_item_versions_settings_model import BackupItemVersionsSettingsModel
        from ..models.file_backup_notification_settings_model import FileBackupNotificationSettingsModel
        from ..models.file_backup_storage_settings_model import FileBackupStorageSettingsModel
        from ..models.job_scripts_settings_model import JobScriptsSettingsModel

        d = dict(src_dict)
        _object_versions = d.pop("objectVersions", UNSET)
        object_versions: Union[Unset, BackupItemVersionsSettingsModel]
        if isinstance(_object_versions, Unset):
            object_versions = UNSET
        else:
            object_versions = BackupItemVersionsSettingsModel.from_dict(_object_versions)

        _storage_data = d.pop("storageData", UNSET)
        storage_data: Union[Unset, FileBackupStorageSettingsModel]
        if isinstance(_storage_data, Unset):
            storage_data = UNSET
        else:
            storage_data = FileBackupStorageSettingsModel.from_dict(_storage_data)

        _backup_health = d.pop("backupHealth", UNSET)
        backup_health: Union[Unset, BackupHealthCheckSettingsModels]
        if isinstance(_backup_health, Unset):
            backup_health = UNSET
        else:
            backup_health = BackupHealthCheckSettingsModels.from_dict(_backup_health)

        _scripts = d.pop("scripts", UNSET)
        scripts: Union[Unset, JobScriptsSettingsModel]
        if isinstance(_scripts, Unset):
            scripts = UNSET
        else:
            scripts = JobScriptsSettingsModel.from_dict(_scripts)

        _notifications = d.pop("notifications", UNSET)
        notifications: Union[Unset, FileBackupNotificationSettingsModel]
        if isinstance(_notifications, Unset):
            notifications = UNSET
        else:
            notifications = FileBackupNotificationSettingsModel.from_dict(_notifications)

        object_storage_backup_job_advanced_settings_model = cls(
            object_versions=object_versions,
            storage_data=storage_data,
            backup_health=backup_health,
            scripts=scripts,
            notifications=notifications,
        )

        object_storage_backup_job_advanced_settings_model.additional_properties = d
        return object_storage_backup_job_advanced_settings_model

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
