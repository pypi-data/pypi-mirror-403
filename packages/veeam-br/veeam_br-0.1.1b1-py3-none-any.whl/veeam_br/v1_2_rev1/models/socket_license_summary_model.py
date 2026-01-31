from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_license_package_type import ELicensePackageType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.socket_license_workload_model import SocketLicenseWorkloadModel


T = TypeVar("T", bound="SocketLicenseSummaryModel")


@_attrs_define
class SocketLicenseSummaryModel:
    """Details on per-socket license usage.

    Attributes:
        licensed_sockets_number (int): Total number of CPU sockets on protected hosts.
        used_sockets_number (int): Number of CPU sockets that have already been used.
        remaining_sockets_number (int): Number of CPU sockets that remain available.
        workload (Union[Unset, list['SocketLicenseWorkloadModel']]): Array of licensed hosts.
        package (Union[Unset, ELicensePackageType]): License package.
    """

    licensed_sockets_number: int
    used_sockets_number: int
    remaining_sockets_number: int
    workload: Union[Unset, list["SocketLicenseWorkloadModel"]] = UNSET
    package: Union[Unset, ELicensePackageType] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        licensed_sockets_number = self.licensed_sockets_number

        used_sockets_number = self.used_sockets_number

        remaining_sockets_number = self.remaining_sockets_number

        workload: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.workload, Unset):
            workload = []
            for workload_item_data in self.workload:
                workload_item = workload_item_data.to_dict()
                workload.append(workload_item)

        package: Union[Unset, str] = UNSET
        if not isinstance(self.package, Unset):
            package = self.package.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "licensedSocketsNumber": licensed_sockets_number,
                "usedSocketsNumber": used_sockets_number,
                "remainingSocketsNumber": remaining_sockets_number,
            }
        )
        if workload is not UNSET:
            field_dict["workload"] = workload
        if package is not UNSET:
            field_dict["package"] = package

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.socket_license_workload_model import SocketLicenseWorkloadModel

        d = dict(src_dict)
        licensed_sockets_number = d.pop("licensedSocketsNumber")

        used_sockets_number = d.pop("usedSocketsNumber")

        remaining_sockets_number = d.pop("remainingSocketsNumber")

        workload = []
        _workload = d.pop("workload", UNSET)
        for workload_item_data in _workload or []:
            workload_item = SocketLicenseWorkloadModel.from_dict(workload_item_data)

            workload.append(workload_item)

        _package = d.pop("package", UNSET)
        package: Union[Unset, ELicensePackageType]
        if isinstance(_package, Unset):
            package = UNSET
        else:
            package = ELicensePackageType(_package)

        socket_license_summary_model = cls(
            licensed_sockets_number=licensed_sockets_number,
            used_sockets_number=used_sockets_number,
            remaining_sockets_number=remaining_sockets_number,
            workload=workload,
            package=package,
        )

        socket_license_summary_model.additional_properties = d
        return socket_license_summary_model

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
