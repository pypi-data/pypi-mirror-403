from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.host_component_port_model import HostComponentPortModel


T = TypeVar("T", bound="LinuxHostSSHSettingsModel")


@_attrs_define
class LinuxHostSSHSettingsModel:
    """SSH settings of the Linux host.

    Attributes:
        components (Union[Unset, list['HostComponentPortModel']]): Array of ports used by Veeam Backup & Replication
            components.
        ssh_time_out_ms (Union[Unset, int]): SSH timeout, in ms. If a task targeted at the server is inactive after the
            timeout, the task is terminated.
        port_range_start (Union[Unset, int]): Start port used for data transfer.
        port_range_end (Union[Unset, int]): End port used for data transfer.
        server_side (Union[Unset, bool]): If `true`, the server is run on this side.
    """

    components: Union[Unset, list["HostComponentPortModel"]] = UNSET
    ssh_time_out_ms: Union[Unset, int] = UNSET
    port_range_start: Union[Unset, int] = UNSET
    port_range_end: Union[Unset, int] = UNSET
    server_side: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        components: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.components, Unset):
            components = []
            for components_item_data in self.components:
                components_item = components_item_data.to_dict()
                components.append(components_item)

        ssh_time_out_ms = self.ssh_time_out_ms

        port_range_start = self.port_range_start

        port_range_end = self.port_range_end

        server_side = self.server_side

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if components is not UNSET:
            field_dict["components"] = components
        if ssh_time_out_ms is not UNSET:
            field_dict["sshTimeOutMs"] = ssh_time_out_ms
        if port_range_start is not UNSET:
            field_dict["portRangeStart"] = port_range_start
        if port_range_end is not UNSET:
            field_dict["portRangeEnd"] = port_range_end
        if server_side is not UNSET:
            field_dict["serverSide"] = server_side

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.host_component_port_model import HostComponentPortModel

        d = dict(src_dict)
        components = []
        _components = d.pop("components", UNSET)
        for components_item_data in _components or []:
            components_item = HostComponentPortModel.from_dict(components_item_data)

            components.append(components_item)

        ssh_time_out_ms = d.pop("sshTimeOutMs", UNSET)

        port_range_start = d.pop("portRangeStart", UNSET)

        port_range_end = d.pop("portRangeEnd", UNSET)

        server_side = d.pop("serverSide", UNSET)

        linux_host_ssh_settings_model = cls(
            components=components,
            ssh_time_out_ms=ssh_time_out_ms,
            port_range_start=port_range_start,
            port_range_end=port_range_end,
            server_side=server_side,
        )

        linux_host_ssh_settings_model.additional_properties = d
        return linux_host_ssh_settings_model

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
