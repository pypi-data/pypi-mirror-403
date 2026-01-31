from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_copy_job_notification_settings_model import BackupCopyJobNotificationSettingsModel
    from ..models.backup_copy_job_rpo_monitor_model import BackupCopyJobRPOMonitorModel
    from ..models.backup_copy_job_storage_settings_model import BackupCopyJobStorageSettingsModel
    from ..models.backup_health_check_settings_models import BackupHealthCheckSettingsModels
    from ..models.full_backup_maintenance_model import FullBackupMaintenanceModel
    from ..models.job_scripts_settings_model import JobScriptsSettingsModel


T = TypeVar("T", bound="BackupCopyJobAdvancedSettingsModel")


@_attrs_define
class BackupCopyJobAdvancedSettingsModel:
    """Advanced settings for backup copy job.

    Attributes:
        backup_health (Union[Unset, BackupHealthCheckSettingsModels]): Health check settings for the latest restore
            point in the backup chain.
        full_backup_maintenance (Union[Unset, FullBackupMaintenanceModel]): Maintenance settings for full backup files.
        storage_data (Union[Unset, BackupCopyJobStorageSettingsModel]): Storage settings for backup copy job.
        rpo_monitor (Union[Unset, BackupCopyJobRPOMonitorModel]): RPO monitor settings for backup copy job.
        notifications (Union[Unset, BackupCopyJobNotificationSettingsModel]): Notification settings.
        scripts (Union[Unset, JobScriptsSettingsModel]): Script settings.<ul><li>`preCommand` — script executed before
            the job</li><li>`postCommand` — script executed after the job</li></ul>
        use_most_recent_restore_point (Union[Unset, bool]): If `true`, process the most recent restore point instead of
            waiting for `periodic mode`.
    """

    backup_health: Union[Unset, "BackupHealthCheckSettingsModels"] = UNSET
    full_backup_maintenance: Union[Unset, "FullBackupMaintenanceModel"] = UNSET
    storage_data: Union[Unset, "BackupCopyJobStorageSettingsModel"] = UNSET
    rpo_monitor: Union[Unset, "BackupCopyJobRPOMonitorModel"] = UNSET
    notifications: Union[Unset, "BackupCopyJobNotificationSettingsModel"] = UNSET
    scripts: Union[Unset, "JobScriptsSettingsModel"] = UNSET
    use_most_recent_restore_point: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        backup_health: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.backup_health, Unset):
            backup_health = self.backup_health.to_dict()

        full_backup_maintenance: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.full_backup_maintenance, Unset):
            full_backup_maintenance = self.full_backup_maintenance.to_dict()

        storage_data: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.storage_data, Unset):
            storage_data = self.storage_data.to_dict()

        rpo_monitor: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.rpo_monitor, Unset):
            rpo_monitor = self.rpo_monitor.to_dict()

        notifications: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.notifications, Unset):
            notifications = self.notifications.to_dict()

        scripts: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.scripts, Unset):
            scripts = self.scripts.to_dict()

        use_most_recent_restore_point = self.use_most_recent_restore_point

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if backup_health is not UNSET:
            field_dict["backupHealth"] = backup_health
        if full_backup_maintenance is not UNSET:
            field_dict["fullBackupMaintenance"] = full_backup_maintenance
        if storage_data is not UNSET:
            field_dict["storageData"] = storage_data
        if rpo_monitor is not UNSET:
            field_dict["rpoMonitor"] = rpo_monitor
        if notifications is not UNSET:
            field_dict["notifications"] = notifications
        if scripts is not UNSET:
            field_dict["scripts"] = scripts
        if use_most_recent_restore_point is not UNSET:
            field_dict["useMostRecentRestorePoint"] = use_most_recent_restore_point

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_copy_job_notification_settings_model import BackupCopyJobNotificationSettingsModel
        from ..models.backup_copy_job_rpo_monitor_model import BackupCopyJobRPOMonitorModel
        from ..models.backup_copy_job_storage_settings_model import BackupCopyJobStorageSettingsModel
        from ..models.backup_health_check_settings_models import BackupHealthCheckSettingsModels
        from ..models.full_backup_maintenance_model import FullBackupMaintenanceModel
        from ..models.job_scripts_settings_model import JobScriptsSettingsModel

        d = dict(src_dict)
        _backup_health = d.pop("backupHealth", UNSET)
        backup_health: Union[Unset, BackupHealthCheckSettingsModels]
        if isinstance(_backup_health, Unset):
            backup_health = UNSET
        else:
            backup_health = BackupHealthCheckSettingsModels.from_dict(_backup_health)

        _full_backup_maintenance = d.pop("fullBackupMaintenance", UNSET)
        full_backup_maintenance: Union[Unset, FullBackupMaintenanceModel]
        if isinstance(_full_backup_maintenance, Unset):
            full_backup_maintenance = UNSET
        else:
            full_backup_maintenance = FullBackupMaintenanceModel.from_dict(_full_backup_maintenance)

        _storage_data = d.pop("storageData", UNSET)
        storage_data: Union[Unset, BackupCopyJobStorageSettingsModel]
        if isinstance(_storage_data, Unset):
            storage_data = UNSET
        else:
            storage_data = BackupCopyJobStorageSettingsModel.from_dict(_storage_data)

        _rpo_monitor = d.pop("rpoMonitor", UNSET)
        rpo_monitor: Union[Unset, BackupCopyJobRPOMonitorModel]
        if isinstance(_rpo_monitor, Unset):
            rpo_monitor = UNSET
        else:
            rpo_monitor = BackupCopyJobRPOMonitorModel.from_dict(_rpo_monitor)

        _notifications = d.pop("notifications", UNSET)
        notifications: Union[Unset, BackupCopyJobNotificationSettingsModel]
        if isinstance(_notifications, Unset):
            notifications = UNSET
        else:
            notifications = BackupCopyJobNotificationSettingsModel.from_dict(_notifications)

        _scripts = d.pop("scripts", UNSET)
        scripts: Union[Unset, JobScriptsSettingsModel]
        if isinstance(_scripts, Unset):
            scripts = UNSET
        else:
            scripts = JobScriptsSettingsModel.from_dict(_scripts)

        use_most_recent_restore_point = d.pop("useMostRecentRestorePoint", UNSET)

        backup_copy_job_advanced_settings_model = cls(
            backup_health=backup_health,
            full_backup_maintenance=full_backup_maintenance,
            storage_data=storage_data,
            rpo_monitor=rpo_monitor,
            notifications=notifications,
            scripts=scripts,
            use_most_recent_restore_point=use_most_recent_restore_point,
        )

        backup_copy_job_advanced_settings_model.additional_properties = d
        return backup_copy_job_advanced_settings_model

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
