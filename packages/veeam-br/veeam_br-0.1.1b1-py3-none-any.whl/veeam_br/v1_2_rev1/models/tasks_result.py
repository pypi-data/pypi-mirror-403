from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.common_task_model import CommonTaskModel
    from ..models.flr_download_task_model import FlrDownloadTaskModel
    from ..models.flr_restore_task_model import FlrRestoreTaskModel
    from ..models.flr_search_task_model import FlrSearchTaskModel
    from ..models.hierarchy_rescan_task_model import HierarchyRescanTaskModel
    from ..models.pagination_result import PaginationResult


T = TypeVar("T", bound="TasksResult")


@_attrs_define
class TasksResult:
    """
    Attributes:
        data (list[Union['CommonTaskModel', 'FlrDownloadTaskModel', 'FlrRestoreTaskModel', 'FlrSearchTaskModel',
            'HierarchyRescanTaskModel']]): Array of tasks.
        pagination (PaginationResult): Pagination settings.
    """

    data: list[
        Union[
            "CommonTaskModel",
            "FlrDownloadTaskModel",
            "FlrRestoreTaskModel",
            "FlrSearchTaskModel",
            "HierarchyRescanTaskModel",
        ]
    ]
    pagination: "PaginationResult"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.common_task_model import CommonTaskModel
        from ..models.flr_download_task_model import FlrDownloadTaskModel
        from ..models.flr_restore_task_model import FlrRestoreTaskModel
        from ..models.flr_search_task_model import FlrSearchTaskModel

        data = []
        for data_item_data in self.data:
            data_item: dict[str, Any]
            if isinstance(data_item_data, CommonTaskModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, FlrRestoreTaskModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, FlrDownloadTaskModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, FlrSearchTaskModel):
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
        from ..models.common_task_model import CommonTaskModel
        from ..models.flr_download_task_model import FlrDownloadTaskModel
        from ..models.flr_restore_task_model import FlrRestoreTaskModel
        from ..models.flr_search_task_model import FlrSearchTaskModel
        from ..models.hierarchy_rescan_task_model import HierarchyRescanTaskModel
        from ..models.pagination_result import PaginationResult

        d = dict(src_dict)
        data = []
        _data = d.pop("data")
        for data_item_data in _data:

            def _parse_data_item(
                data: object,
            ) -> Union[
                "CommonTaskModel",
                "FlrDownloadTaskModel",
                "FlrRestoreTaskModel",
                "FlrSearchTaskModel",
                "HierarchyRescanTaskModel",
            ]:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_task_model_type_0 = CommonTaskModel.from_dict(data)

                    return componentsschemas_task_model_type_0
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_task_model_type_1 = FlrRestoreTaskModel.from_dict(data)

                    return componentsschemas_task_model_type_1
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_task_model_type_2 = FlrDownloadTaskModel.from_dict(data)

                    return componentsschemas_task_model_type_2
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_task_model_type_3 = FlrSearchTaskModel.from_dict(data)

                    return componentsschemas_task_model_type_3
                except:  # noqa: E722
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_task_model_type_4 = HierarchyRescanTaskModel.from_dict(data)

                return componentsschemas_task_model_type_4

            data_item = _parse_data_item(data_item_data)

            data.append(data_item)

        pagination = PaginationResult.from_dict(d.pop("pagination"))

        tasks_result = cls(
            data=data,
            pagination=pagination,
        )

        tasks_result.additional_properties = d
        return tasks_result

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
