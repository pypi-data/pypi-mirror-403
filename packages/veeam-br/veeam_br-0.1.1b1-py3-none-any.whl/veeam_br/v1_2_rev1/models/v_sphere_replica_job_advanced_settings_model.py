from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backup_job_advanced_settings_v_sphere_model import BackupJobAdvancedSettingsVSphereModel
    from ..models.job_scripts_settings_model import JobScriptsSettingsModel
    from ..models.primary_storage_integration_settings_model import PrimaryStorageIntegrationSettingsModel
    from ..models.replica_notification_settings_model import ReplicaNotificationSettingsModel
    from ..models.replica_traffic_settings_model import ReplicaTrafficSettingsModel


T = TypeVar("T", bound="VSphereReplicaJobAdvancedSettingsModel")


@_attrs_define
class VSphereReplicaJobAdvancedSettingsModel:
    """Advanced job settings.

    Attributes:
        traffic (Union[Unset, ReplicaTrafficSettingsModel]): Traffic settings.
        notifications (Union[Unset, ReplicaNotificationSettingsModel]): Notification settings.
        v_sphere (Union[Unset, BackupJobAdvancedSettingsVSphereModel]): VMware vSphere settings for the job.
        integration (Union[Unset, PrimaryStorageIntegrationSettingsModel]): Primary storage integration settings for the
            job.
        scripts (Union[Unset, JobScriptsSettingsModel]): Script settings.<ul><li>`preCommand` — script executed before
            the job</li><li>`postCommand` — script executed after the job</li></ul>
    """

    traffic: Union[Unset, "ReplicaTrafficSettingsModel"] = UNSET
    notifications: Union[Unset, "ReplicaNotificationSettingsModel"] = UNSET
    v_sphere: Union[Unset, "BackupJobAdvancedSettingsVSphereModel"] = UNSET
    integration: Union[Unset, "PrimaryStorageIntegrationSettingsModel"] = UNSET
    scripts: Union[Unset, "JobScriptsSettingsModel"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        traffic: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.traffic, Unset):
            traffic = self.traffic.to_dict()

        notifications: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.notifications, Unset):
            notifications = self.notifications.to_dict()

        v_sphere: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.v_sphere, Unset):
            v_sphere = self.v_sphere.to_dict()

        integration: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.integration, Unset):
            integration = self.integration.to_dict()

        scripts: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.scripts, Unset):
            scripts = self.scripts.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if traffic is not UNSET:
            field_dict["traffic"] = traffic
        if notifications is not UNSET:
            field_dict["notifications"] = notifications
        if v_sphere is not UNSET:
            field_dict["vSphere"] = v_sphere
        if integration is not UNSET:
            field_dict["integration"] = integration
        if scripts is not UNSET:
            field_dict["scripts"] = scripts

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backup_job_advanced_settings_v_sphere_model import BackupJobAdvancedSettingsVSphereModel
        from ..models.job_scripts_settings_model import JobScriptsSettingsModel
        from ..models.primary_storage_integration_settings_model import PrimaryStorageIntegrationSettingsModel
        from ..models.replica_notification_settings_model import ReplicaNotificationSettingsModel
        from ..models.replica_traffic_settings_model import ReplicaTrafficSettingsModel

        d = dict(src_dict)
        _traffic = d.pop("traffic", UNSET)
        traffic: Union[Unset, ReplicaTrafficSettingsModel]
        if isinstance(_traffic, Unset):
            traffic = UNSET
        else:
            traffic = ReplicaTrafficSettingsModel.from_dict(_traffic)

        _notifications = d.pop("notifications", UNSET)
        notifications: Union[Unset, ReplicaNotificationSettingsModel]
        if isinstance(_notifications, Unset):
            notifications = UNSET
        else:
            notifications = ReplicaNotificationSettingsModel.from_dict(_notifications)

        _v_sphere = d.pop("vSphere", UNSET)
        v_sphere: Union[Unset, BackupJobAdvancedSettingsVSphereModel]
        if isinstance(_v_sphere, Unset):
            v_sphere = UNSET
        else:
            v_sphere = BackupJobAdvancedSettingsVSphereModel.from_dict(_v_sphere)

        _integration = d.pop("integration", UNSET)
        integration: Union[Unset, PrimaryStorageIntegrationSettingsModel]
        if isinstance(_integration, Unset):
            integration = UNSET
        else:
            integration = PrimaryStorageIntegrationSettingsModel.from_dict(_integration)

        _scripts = d.pop("scripts", UNSET)
        scripts: Union[Unset, JobScriptsSettingsModel]
        if isinstance(_scripts, Unset):
            scripts = UNSET
        else:
            scripts = JobScriptsSettingsModel.from_dict(_scripts)

        v_sphere_replica_job_advanced_settings_model = cls(
            traffic=traffic,
            notifications=notifications,
            v_sphere=v_sphere,
            integration=integration,
            scripts=scripts,
        )

        v_sphere_replica_job_advanced_settings_model.additional_properties = d
        return v_sphere_replica_job_advanced_settings_model

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
