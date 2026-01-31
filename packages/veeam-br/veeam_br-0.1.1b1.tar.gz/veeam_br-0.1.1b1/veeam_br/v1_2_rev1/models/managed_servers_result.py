from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.cloud_director_host_model import CloudDirectorHostModel
    from ..models.linux_host_model import LinuxHostModel
    from ..models.pagination_result import PaginationResult
    from ..models.vi_host_model import ViHostModel
    from ..models.windows_host_model import WindowsHostModel


T = TypeVar("T", bound="ManagedServersResult")


@_attrs_define
class ManagedServersResult:
    """
    Attributes:
        data (list[Union['CloudDirectorHostModel', 'LinuxHostModel', 'ViHostModel', 'WindowsHostModel']]): Array of
            managed servers.
        pagination (PaginationResult): Pagination settings.
    """

    data: list[Union["CloudDirectorHostModel", "LinuxHostModel", "ViHostModel", "WindowsHostModel"]]
    pagination: "PaginationResult"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.linux_host_model import LinuxHostModel
        from ..models.vi_host_model import ViHostModel
        from ..models.windows_host_model import WindowsHostModel

        data = []
        for data_item_data in self.data:
            data_item: dict[str, Any]
            if isinstance(data_item_data, WindowsHostModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, LinuxHostModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, ViHostModel):
                data_item = data_item_data.to_dict()
            else:
                data_item = data_item_data.to_dict()

            data.append(data_item)

        pagination = self.pagination.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
                "pagination": pagination,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_director_host_model import CloudDirectorHostModel
        from ..models.linux_host_model import LinuxHostModel
        from ..models.pagination_result import PaginationResult
        from ..models.vi_host_model import ViHostModel
        from ..models.windows_host_model import WindowsHostModel

        d = dict(src_dict)
        data = []
        _data = d.pop("data")
        for data_item_data in _data:

            def _parse_data_item(
                data: object,
            ) -> Union["CloudDirectorHostModel", "LinuxHostModel", "ViHostModel", "WindowsHostModel"]:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_managed_server_model_type_0 = WindowsHostModel.from_dict(data)

                    return componentsschemas_managed_server_model_type_0
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_managed_server_model_type_1 = LinuxHostModel.from_dict(data)

                    return componentsschemas_managed_server_model_type_1
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_managed_server_model_type_2 = ViHostModel.from_dict(data)

                    return componentsschemas_managed_server_model_type_2
                except:  # noqa: E722
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_managed_server_model_type_3 = CloudDirectorHostModel.from_dict(data)

                return componentsschemas_managed_server_model_type_3

            data_item = _parse_data_item(data_item_data)

            data.append(data_item)

        pagination = PaginationResult.from_dict(d.pop("pagination"))

        managed_servers_result = cls(
            data=data,
            pagination=pagination,
        )

        managed_servers_result.additional_properties = d
        return managed_servers_result

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
