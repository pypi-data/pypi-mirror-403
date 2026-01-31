import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_suspicious_activity_events_filters_order_column import ESuspiciousActivityEventsFiltersOrderColumn
from ..models.e_suspicious_activity_severity import ESuspiciousActivitySeverity
from ..models.e_suspicious_activity_source_type import ESuspiciousActivitySourceType
from ..models.e_suspicious_activity_state import ESuspiciousActivityState
from ..models.e_suspicious_activity_type import ESuspiciousActivityType
from ..types import UNSET, Unset

T = TypeVar("T", bound="SuspiciousActivityEventsFilters")


@_attrs_define
class SuspiciousActivityEventsFilters:
    """SuspiciousActivityEventsFilters

    Attributes:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):
        order_column (Union[Unset, ESuspiciousActivityEventsFiltersOrderColumn]):
            ESuspiciousActivityEventsFiltersOrderColumn.
        order_asc (Union[Unset, bool]):
        type_filter (Union[Unset, list[ESuspiciousActivityType]]):
        detected_after_time_utc_filter (Union[Unset, datetime.datetime]):
        detected_before_time_utc_filter (Union[Unset, datetime.datetime]):
        created_after_time_utc_filter (Union[Unset, datetime.datetime]):
        created_before_time_utc_filter (Union[Unset, datetime.datetime]):
        backup_object_id_filter (Union[Unset, UUID]):
        state_filter (Union[Unset, list[ESuspiciousActivityState]]):
        source_filter (Union[Unset, list[ESuspiciousActivitySourceType]]):
        severity_filter (Union[Unset, list[ESuspiciousActivitySeverity]]):
        created_by_filter (Union[Unset, str]):
        engine_filter (Union[Unset, str]):
        machine_name_filter (Union[Unset, str]):
    """

    skip: Union[Unset, int] = UNSET
    limit: Union[Unset, int] = UNSET
    order_column: Union[Unset, ESuspiciousActivityEventsFiltersOrderColumn] = UNSET
    order_asc: Union[Unset, bool] = UNSET
    type_filter: Union[Unset, list[ESuspiciousActivityType]] = UNSET
    detected_after_time_utc_filter: Union[Unset, datetime.datetime] = UNSET
    detected_before_time_utc_filter: Union[Unset, datetime.datetime] = UNSET
    created_after_time_utc_filter: Union[Unset, datetime.datetime] = UNSET
    created_before_time_utc_filter: Union[Unset, datetime.datetime] = UNSET
    backup_object_id_filter: Union[Unset, UUID] = UNSET
    state_filter: Union[Unset, list[ESuspiciousActivityState]] = UNSET
    source_filter: Union[Unset, list[ESuspiciousActivitySourceType]] = UNSET
    severity_filter: Union[Unset, list[ESuspiciousActivitySeverity]] = UNSET
    created_by_filter: Union[Unset, str] = UNSET
    engine_filter: Union[Unset, str] = UNSET
    machine_name_filter: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: Union[Unset, str] = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        type_filter: Union[Unset, list[str]] = UNSET
        if not isinstance(self.type_filter, Unset):
            type_filter = []
            for type_filter_item_data in self.type_filter:
                type_filter_item = type_filter_item_data.value
                type_filter.append(type_filter_item)

        detected_after_time_utc_filter: Union[Unset, str] = UNSET
        if not isinstance(self.detected_after_time_utc_filter, Unset):
            detected_after_time_utc_filter = self.detected_after_time_utc_filter.isoformat()

        detected_before_time_utc_filter: Union[Unset, str] = UNSET
        if not isinstance(self.detected_before_time_utc_filter, Unset):
            detected_before_time_utc_filter = self.detected_before_time_utc_filter.isoformat()

        created_after_time_utc_filter: Union[Unset, str] = UNSET
        if not isinstance(self.created_after_time_utc_filter, Unset):
            created_after_time_utc_filter = self.created_after_time_utc_filter.isoformat()

        created_before_time_utc_filter: Union[Unset, str] = UNSET
        if not isinstance(self.created_before_time_utc_filter, Unset):
            created_before_time_utc_filter = self.created_before_time_utc_filter.isoformat()

        backup_object_id_filter: Union[Unset, str] = UNSET
        if not isinstance(self.backup_object_id_filter, Unset):
            backup_object_id_filter = str(self.backup_object_id_filter)

        state_filter: Union[Unset, list[str]] = UNSET
        if not isinstance(self.state_filter, Unset):
            state_filter = []
            for state_filter_item_data in self.state_filter:
                state_filter_item = state_filter_item_data.value
                state_filter.append(state_filter_item)

        source_filter: Union[Unset, list[str]] = UNSET
        if not isinstance(self.source_filter, Unset):
            source_filter = []
            for source_filter_item_data in self.source_filter:
                source_filter_item = source_filter_item_data.value
                source_filter.append(source_filter_item)

        severity_filter: Union[Unset, list[str]] = UNSET
        if not isinstance(self.severity_filter, Unset):
            severity_filter = []
            for severity_filter_item_data in self.severity_filter:
                severity_filter_item = severity_filter_item_data.value
                severity_filter.append(severity_filter_item)

        created_by_filter = self.created_by_filter

        engine_filter = self.engine_filter

        machine_name_filter = self.machine_name_filter

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if skip is not UNSET:
            field_dict["skip"] = skip
        if limit is not UNSET:
            field_dict["limit"] = limit
        if order_column is not UNSET:
            field_dict["orderColumn"] = order_column
        if order_asc is not UNSET:
            field_dict["orderAsc"] = order_asc
        if type_filter is not UNSET:
            field_dict["typeFilter"] = type_filter
        if detected_after_time_utc_filter is not UNSET:
            field_dict["detectedAfterTimeUtcFilter"] = detected_after_time_utc_filter
        if detected_before_time_utc_filter is not UNSET:
            field_dict["detectedBeforeTimeUtcFilter"] = detected_before_time_utc_filter
        if created_after_time_utc_filter is not UNSET:
            field_dict["createdAfterTimeUtcFilter"] = created_after_time_utc_filter
        if created_before_time_utc_filter is not UNSET:
            field_dict["createdBeforeTimeUtcFilter"] = created_before_time_utc_filter
        if backup_object_id_filter is not UNSET:
            field_dict["backupObjectIdFilter"] = backup_object_id_filter
        if state_filter is not UNSET:
            field_dict["stateFilter"] = state_filter
        if source_filter is not UNSET:
            field_dict["sourceFilter"] = source_filter
        if severity_filter is not UNSET:
            field_dict["severityFilter"] = severity_filter
        if created_by_filter is not UNSET:
            field_dict["createdByFilter"] = created_by_filter
        if engine_filter is not UNSET:
            field_dict["engineFilter"] = engine_filter
        if machine_name_filter is not UNSET:
            field_dict["machineNameFilter"] = machine_name_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: Union[Unset, ESuspiciousActivityEventsFiltersOrderColumn]
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = ESuspiciousActivityEventsFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        type_filter = []
        _type_filter = d.pop("typeFilter", UNSET)
        for type_filter_item_data in _type_filter or []:
            type_filter_item = ESuspiciousActivityType(type_filter_item_data)

            type_filter.append(type_filter_item)

        _detected_after_time_utc_filter = d.pop("detectedAfterTimeUtcFilter", UNSET)
        detected_after_time_utc_filter: Union[Unset, datetime.datetime]
        if isinstance(_detected_after_time_utc_filter, Unset):
            detected_after_time_utc_filter = UNSET
        else:
            detected_after_time_utc_filter = isoparse(_detected_after_time_utc_filter)

        _detected_before_time_utc_filter = d.pop("detectedBeforeTimeUtcFilter", UNSET)
        detected_before_time_utc_filter: Union[Unset, datetime.datetime]
        if isinstance(_detected_before_time_utc_filter, Unset):
            detected_before_time_utc_filter = UNSET
        else:
            detected_before_time_utc_filter = isoparse(_detected_before_time_utc_filter)

        _created_after_time_utc_filter = d.pop("createdAfterTimeUtcFilter", UNSET)
        created_after_time_utc_filter: Union[Unset, datetime.datetime]
        if isinstance(_created_after_time_utc_filter, Unset):
            created_after_time_utc_filter = UNSET
        else:
            created_after_time_utc_filter = isoparse(_created_after_time_utc_filter)

        _created_before_time_utc_filter = d.pop("createdBeforeTimeUtcFilter", UNSET)
        created_before_time_utc_filter: Union[Unset, datetime.datetime]
        if isinstance(_created_before_time_utc_filter, Unset):
            created_before_time_utc_filter = UNSET
        else:
            created_before_time_utc_filter = isoparse(_created_before_time_utc_filter)

        _backup_object_id_filter = d.pop("backupObjectIdFilter", UNSET)
        backup_object_id_filter: Union[Unset, UUID]
        if isinstance(_backup_object_id_filter, Unset):
            backup_object_id_filter = UNSET
        else:
            backup_object_id_filter = UUID(_backup_object_id_filter)

        state_filter = []
        _state_filter = d.pop("stateFilter", UNSET)
        for state_filter_item_data in _state_filter or []:
            state_filter_item = ESuspiciousActivityState(state_filter_item_data)

            state_filter.append(state_filter_item)

        source_filter = []
        _source_filter = d.pop("sourceFilter", UNSET)
        for source_filter_item_data in _source_filter or []:
            source_filter_item = ESuspiciousActivitySourceType(source_filter_item_data)

            source_filter.append(source_filter_item)

        severity_filter = []
        _severity_filter = d.pop("severityFilter", UNSET)
        for severity_filter_item_data in _severity_filter or []:
            severity_filter_item = ESuspiciousActivitySeverity(severity_filter_item_data)

            severity_filter.append(severity_filter_item)

        created_by_filter = d.pop("createdByFilter", UNSET)

        engine_filter = d.pop("engineFilter", UNSET)

        machine_name_filter = d.pop("machineNameFilter", UNSET)

        suspicious_activity_events_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            type_filter=type_filter,
            detected_after_time_utc_filter=detected_after_time_utc_filter,
            detected_before_time_utc_filter=detected_before_time_utc_filter,
            created_after_time_utc_filter=created_after_time_utc_filter,
            created_before_time_utc_filter=created_before_time_utc_filter,
            backup_object_id_filter=backup_object_id_filter,
            state_filter=state_filter,
            source_filter=source_filter,
            severity_filter=severity_filter,
            created_by_filter=created_by_filter,
            engine_filter=engine_filter,
            machine_name_filter=machine_name_filter,
        )

        suspicious_activity_events_filters.additional_properties = d
        return suspicious_activity_events_filters

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
