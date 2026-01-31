from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.hyper_v_linux_flr_helper_appliance_resource_model import HyperVLinuxFlrHelperApplianceResourceModel
    from ..models.ip_settings_model import IpSettingsModel
    from ..models.vmware_linux_flr_helper_appliance_resource_model import VmwareLinuxFlrHelperApplianceResourceModel


T = TypeVar("T", bound="LinuxFlrHelperApplianceSpec")


@_attrs_define
class LinuxFlrHelperApplianceSpec:
    """Helper appliance settings. Use this option if you want to mount the file system to a temporary helper appliance.

    Attributes:
        platform_resource_settings (Union['HyperVLinuxFlrHelperApplianceResourceModel',
            'VmwareLinuxFlrHelperApplianceResourceModel', Unset]): Helper appliance location.
        network_settings (Union[Unset, IpSettingsModel]): IP addressing settings for the helper appliance and DNS
            server.
        ftp_server_enabled (Union[Unset, bool]): If `true`, FTP access to the restored file system is enabled.
        restore_from_nss (Union[Unset, bool]): If `true`, the file system of the original machine is Novell Storage
            Services (NSS).
    """

    platform_resource_settings: Union[
        "HyperVLinuxFlrHelperApplianceResourceModel", "VmwareLinuxFlrHelperApplianceResourceModel", Unset
    ] = UNSET
    network_settings: Union[Unset, "IpSettingsModel"] = UNSET
    ftp_server_enabled: Union[Unset, bool] = UNSET
    restore_from_nss: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.vmware_linux_flr_helper_appliance_resource_model import VmwareLinuxFlrHelperApplianceResourceModel

        platform_resource_settings: Union[Unset, dict[str, Any]]
        if isinstance(self.platform_resource_settings, Unset):
            platform_resource_settings = UNSET
        elif isinstance(self.platform_resource_settings, VmwareLinuxFlrHelperApplianceResourceModel):
            platform_resource_settings = self.platform_resource_settings.to_dict()
        else:
            platform_resource_settings = self.platform_resource_settings.to_dict()

        network_settings: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.network_settings, Unset):
            network_settings = self.network_settings.to_dict()

        ftp_server_enabled = self.ftp_server_enabled

        restore_from_nss = self.restore_from_nss

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if platform_resource_settings is not UNSET:
            field_dict["platformResourceSettings"] = platform_resource_settings
        if network_settings is not UNSET:
            field_dict["networkSettings"] = network_settings
        if ftp_server_enabled is not UNSET:
            field_dict["ftpServerEnabled"] = ftp_server_enabled
        if restore_from_nss is not UNSET:
            field_dict["restoreFromNSS"] = restore_from_nss

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.hyper_v_linux_flr_helper_appliance_resource_model import (
            HyperVLinuxFlrHelperApplianceResourceModel,
        )
        from ..models.ip_settings_model import IpSettingsModel
        from ..models.vmware_linux_flr_helper_appliance_resource_model import VmwareLinuxFlrHelperApplianceResourceModel

        d = dict(src_dict)

        def _parse_platform_resource_settings(
            data: object,
        ) -> Union["HyperVLinuxFlrHelperApplianceResourceModel", "VmwareLinuxFlrHelperApplianceResourceModel", Unset]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_linux_flr_helper_appliance_resource_model_type_0 = (
                    VmwareLinuxFlrHelperApplianceResourceModel.from_dict(data)
                )

                return componentsschemas_linux_flr_helper_appliance_resource_model_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_linux_flr_helper_appliance_resource_model_type_1 = (
                HyperVLinuxFlrHelperApplianceResourceModel.from_dict(data)
            )

            return componentsschemas_linux_flr_helper_appliance_resource_model_type_1

        platform_resource_settings = _parse_platform_resource_settings(d.pop("platformResourceSettings", UNSET))

        _network_settings = d.pop("networkSettings", UNSET)
        network_settings: Union[Unset, IpSettingsModel]
        if isinstance(_network_settings, Unset):
            network_settings = UNSET
        else:
            network_settings = IpSettingsModel.from_dict(_network_settings)

        ftp_server_enabled = d.pop("ftpServerEnabled", UNSET)

        restore_from_nss = d.pop("restoreFromNSS", UNSET)

        linux_flr_helper_appliance_spec = cls(
            platform_resource_settings=platform_resource_settings,
            network_settings=network_settings,
            ftp_server_enabled=ftp_server_enabled,
            restore_from_nss=restore_from_nss,
        )

        linux_flr_helper_appliance_spec.additional_properties = d
        return linux_flr_helper_appliance_spec

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
