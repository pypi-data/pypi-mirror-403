from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.antivirus_task_session_model import AntivirusTaskSessionModel
    from ..models.backup_task_session_model import BackupTaskSessionModel
    from ..models.pagination_result import PaginationResult
    from ..models.replica_task_session_model import ReplicaTaskSessionModel
    from ..models.restore_task_session_model import RestoreTaskSessionModel


T = TypeVar("T", bound="TaskSessionsResult")


@_attrs_define
class TaskSessionsResult:
    """Task sessions settings.

    Attributes:
        data (list[Union['AntivirusTaskSessionModel', 'BackupTaskSessionModel', 'ReplicaTaskSessionModel',
            'RestoreTaskSessionModel']]): Array of task sessions.
        pagination (PaginationResult): Pagination settings.
    """

    data: list[
        Union[
            "AntivirusTaskSessionModel", "BackupTaskSessionModel", "ReplicaTaskSessionModel", "RestoreTaskSessionModel"
        ]
    ]
    pagination: "PaginationResult"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.backup_task_session_model import BackupTaskSessionModel
        from ..models.replica_task_session_model import ReplicaTaskSessionModel
        from ..models.restore_task_session_model import RestoreTaskSessionModel

        data = []
        for data_item_data in self.data:
            data_item: dict[str, Any]
            if isinstance(data_item_data, BackupTaskSessionModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, ReplicaTaskSessionModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, RestoreTaskSessionModel):
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
        from ..models.antivirus_task_session_model import AntivirusTaskSessionModel
        from ..models.backup_task_session_model import BackupTaskSessionModel
        from ..models.pagination_result import PaginationResult
        from ..models.replica_task_session_model import ReplicaTaskSessionModel
        from ..models.restore_task_session_model import RestoreTaskSessionModel

        d = dict(src_dict)
        data = []
        _data = d.pop("data")
        for data_item_data in _data:

            def _parse_data_item(
                data: object,
            ) -> Union[
                "AntivirusTaskSessionModel",
                "BackupTaskSessionModel",
                "ReplicaTaskSessionModel",
                "RestoreTaskSessionModel",
            ]:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_task_session_model_type_0 = BackupTaskSessionModel.from_dict(data)

                    return componentsschemas_task_session_model_type_0
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_task_session_model_type_1 = ReplicaTaskSessionModel.from_dict(data)

                    return componentsschemas_task_session_model_type_1
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_task_session_model_type_2 = RestoreTaskSessionModel.from_dict(data)

                    return componentsschemas_task_session_model_type_2
                except:  # noqa: E722
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_task_session_model_type_3 = AntivirusTaskSessionModel.from_dict(data)

                return componentsschemas_task_session_model_type_3

            data_item = _parse_data_item(data_item_data)

            data.append(data_item)

        pagination = PaginationResult.from_dict(d.pop("pagination"))

        task_sessions_result = cls(
            data=data,
            pagination=pagination,
        )

        task_sessions_result.additional_properties = d
        return task_sessions_result

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
