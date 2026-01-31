from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_application_plugin_type import EApplicationPluginType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.advanced_protection_group_settings_model import AdvancedProtectionGroupSettingsModel
    from ..models.protection_group_options_rescan_schedule_model import ProtectionGroupOptionsRescanScheduleModel


T = TypeVar("T", bound="ProtectionGroupOptionsModel")


@_attrs_define
class ProtectionGroupOptionsModel:
    """Protection group options.

    Attributes:
        rescan_schedule (Union[Unset, ProtectionGroupOptionsRescanScheduleModel]): Rescan schedule settings for the
            protection group.
        distribution_server_id (Union[Unset, UUID]): ID of the Microsoft Windows distribution server from which agent
            packages are deployed.
        distribution_repository_id (Union[Unset, UUID]): ID of the object storage distribution repository from which
            agent packages are deployed.
        install_backup_agent (Union[Unset, bool]): If `true`, the distribution server will deploy packages to the
            discovered computers in the protection group.
        install_cbt_driver (Union[Unset, bool]): If `true`, Changed Block Tracking driver will be deployed to the
            discovered computers protected with Veeam Agent for Microsoft Windows.
        install_application_plugins (Union[Unset, bool]): If `true`, application plug-ins will be deployed to all the
            discovered computers in the protection group.
        application_plugins (Union[Unset, list[EApplicationPluginType]]): Array of application plug-ins.
        update_automatically (Union[Unset, bool]): If `true`, agents and plug-ins will be automatically upgraded on
            discovered computers.
        reboot_if_required (Union[Unset, bool]): If `true`, Veeam Backup & Replication will reboot a protected computer
            if required.
        advanced_settings (Union[Unset, AdvancedProtectionGroupSettingsModel]): Advanced settings for the protection
            group.
    """

    rescan_schedule: Union[Unset, "ProtectionGroupOptionsRescanScheduleModel"] = UNSET
    distribution_server_id: Union[Unset, UUID] = UNSET
    distribution_repository_id: Union[Unset, UUID] = UNSET
    install_backup_agent: Union[Unset, bool] = UNSET
    install_cbt_driver: Union[Unset, bool] = UNSET
    install_application_plugins: Union[Unset, bool] = UNSET
    application_plugins: Union[Unset, list[EApplicationPluginType]] = UNSET
    update_automatically: Union[Unset, bool] = UNSET
    reboot_if_required: Union[Unset, bool] = UNSET
    advanced_settings: Union[Unset, "AdvancedProtectionGroupSettingsModel"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        rescan_schedule: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.rescan_schedule, Unset):
            rescan_schedule = self.rescan_schedule.to_dict()

        distribution_server_id: Union[Unset, str] = UNSET
        if not isinstance(self.distribution_server_id, Unset):
            distribution_server_id = str(self.distribution_server_id)

        distribution_repository_id: Union[Unset, str] = UNSET
        if not isinstance(self.distribution_repository_id, Unset):
            distribution_repository_id = str(self.distribution_repository_id)

        install_backup_agent = self.install_backup_agent

        install_cbt_driver = self.install_cbt_driver

        install_application_plugins = self.install_application_plugins

        application_plugins: Union[Unset, list[str]] = UNSET
        if not isinstance(self.application_plugins, Unset):
            application_plugins = []
            for application_plugins_item_data in self.application_plugins:
                application_plugins_item = application_plugins_item_data.value
                application_plugins.append(application_plugins_item)

        update_automatically = self.update_automatically

        reboot_if_required = self.reboot_if_required

        advanced_settings: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.advanced_settings, Unset):
            advanced_settings = self.advanced_settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if rescan_schedule is not UNSET:
            field_dict["rescanSchedule"] = rescan_schedule
        if distribution_server_id is not UNSET:
            field_dict["distributionServerId"] = distribution_server_id
        if distribution_repository_id is not UNSET:
            field_dict["distributionRepositoryId"] = distribution_repository_id
        if install_backup_agent is not UNSET:
            field_dict["installBackupAgent"] = install_backup_agent
        if install_cbt_driver is not UNSET:
            field_dict["installCBTDriver"] = install_cbt_driver
        if install_application_plugins is not UNSET:
            field_dict["installApplicationPlugins"] = install_application_plugins
        if application_plugins is not UNSET:
            field_dict["applicationPlugins"] = application_plugins
        if update_automatically is not UNSET:
            field_dict["updateAutomatically"] = update_automatically
        if reboot_if_required is not UNSET:
            field_dict["rebootIfRequired"] = reboot_if_required
        if advanced_settings is not UNSET:
            field_dict["advancedSettings"] = advanced_settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.advanced_protection_group_settings_model import AdvancedProtectionGroupSettingsModel
        from ..models.protection_group_options_rescan_schedule_model import ProtectionGroupOptionsRescanScheduleModel

        d = dict(src_dict)
        _rescan_schedule = d.pop("rescanSchedule", UNSET)
        rescan_schedule: Union[Unset, ProtectionGroupOptionsRescanScheduleModel]
        if isinstance(_rescan_schedule, Unset):
            rescan_schedule = UNSET
        else:
            rescan_schedule = ProtectionGroupOptionsRescanScheduleModel.from_dict(_rescan_schedule)

        _distribution_server_id = d.pop("distributionServerId", UNSET)
        distribution_server_id: Union[Unset, UUID]
        if isinstance(_distribution_server_id, Unset):
            distribution_server_id = UNSET
        else:
            distribution_server_id = UUID(_distribution_server_id)

        _distribution_repository_id = d.pop("distributionRepositoryId", UNSET)
        distribution_repository_id: Union[Unset, UUID]
        if isinstance(_distribution_repository_id, Unset):
            distribution_repository_id = UNSET
        else:
            distribution_repository_id = UUID(_distribution_repository_id)

        install_backup_agent = d.pop("installBackupAgent", UNSET)

        install_cbt_driver = d.pop("installCBTDriver", UNSET)

        install_application_plugins = d.pop("installApplicationPlugins", UNSET)

        application_plugins = []
        _application_plugins = d.pop("applicationPlugins", UNSET)
        for application_plugins_item_data in _application_plugins or []:
            application_plugins_item = EApplicationPluginType(application_plugins_item_data)

            application_plugins.append(application_plugins_item)

        update_automatically = d.pop("updateAutomatically", UNSET)

        reboot_if_required = d.pop("rebootIfRequired", UNSET)

        _advanced_settings = d.pop("advancedSettings", UNSET)
        advanced_settings: Union[Unset, AdvancedProtectionGroupSettingsModel]
        if isinstance(_advanced_settings, Unset):
            advanced_settings = UNSET
        else:
            advanced_settings = AdvancedProtectionGroupSettingsModel.from_dict(_advanced_settings)

        protection_group_options_model = cls(
            rescan_schedule=rescan_schedule,
            distribution_server_id=distribution_server_id,
            distribution_repository_id=distribution_repository_id,
            install_backup_agent=install_backup_agent,
            install_cbt_driver=install_cbt_driver,
            install_application_plugins=install_application_plugins,
            application_plugins=application_plugins,
            update_automatically=update_automatically,
            reboot_if_required=reboot_if_required,
            advanced_settings=advanced_settings,
        )

        protection_group_options_model.additional_properties = d
        return protection_group_options_model

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
