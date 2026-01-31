import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_authorization_event_state import EAuthorizationEventState
from ..models.e_authorization_events_filters_order_column import EAuthorizationEventsFiltersOrderColumn
from ..types import UNSET, Unset

T = TypeVar("T", bound="AuthorizationEventsFilters")


@_attrs_define
class AuthorizationEventsFilters:
    """
    Attributes:
        skip (Union[Unset, int]): Number of task to skip.
        limit (Union[Unset, int]): Maximum number of tasks to return.
        order_column (Union[Unset, EAuthorizationEventsFiltersOrderColumn]):
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        created_after_filter (Union[Unset, datetime.datetime]):
        created_before_filter (Union[Unset, datetime.datetime]):
        processed_after_filter (Union[Unset, datetime.datetime]):
        processed_before_filter (Union[Unset, datetime.datetime]):
        state_filter (Union[Unset, EAuthorizationEventState]): Event state.
        created_by_filter (Union[Unset, str]):
        processed_by_filter (Union[Unset, str]):
        expire_before_filter (Union[Unset, datetime.datetime]):
        expire_after_filter (Union[Unset, datetime.datetime]):
    """

    skip: Union[Unset, int] = UNSET
    limit: Union[Unset, int] = UNSET
    order_column: Union[Unset, EAuthorizationEventsFiltersOrderColumn] = UNSET
    order_asc: Union[Unset, bool] = UNSET
    name_filter: Union[Unset, str] = UNSET
    created_after_filter: Union[Unset, datetime.datetime] = UNSET
    created_before_filter: Union[Unset, datetime.datetime] = UNSET
    processed_after_filter: Union[Unset, datetime.datetime] = UNSET
    processed_before_filter: Union[Unset, datetime.datetime] = UNSET
    state_filter: Union[Unset, EAuthorizationEventState] = UNSET
    created_by_filter: Union[Unset, str] = UNSET
    processed_by_filter: Union[Unset, str] = UNSET
    expire_before_filter: Union[Unset, datetime.datetime] = UNSET
    expire_after_filter: Union[Unset, datetime.datetime] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        limit = self.limit

        order_column: Union[Unset, str] = UNSET
        if not isinstance(self.order_column, Unset):
            order_column = self.order_column.value

        order_asc = self.order_asc

        name_filter = self.name_filter

        created_after_filter: Union[Unset, str] = UNSET
        if not isinstance(self.created_after_filter, Unset):
            created_after_filter = self.created_after_filter.isoformat()

        created_before_filter: Union[Unset, str] = UNSET
        if not isinstance(self.created_before_filter, Unset):
            created_before_filter = self.created_before_filter.isoformat()

        processed_after_filter: Union[Unset, str] = UNSET
        if not isinstance(self.processed_after_filter, Unset):
            processed_after_filter = self.processed_after_filter.isoformat()

        processed_before_filter: Union[Unset, str] = UNSET
        if not isinstance(self.processed_before_filter, Unset):
            processed_before_filter = self.processed_before_filter.isoformat()

        state_filter: Union[Unset, str] = UNSET
        if not isinstance(self.state_filter, Unset):
            state_filter = self.state_filter.value

        created_by_filter = self.created_by_filter

        processed_by_filter = self.processed_by_filter

        expire_before_filter: Union[Unset, str] = UNSET
        if not isinstance(self.expire_before_filter, Unset):
            expire_before_filter = self.expire_before_filter.isoformat()

        expire_after_filter: Union[Unset, str] = UNSET
        if not isinstance(self.expire_after_filter, Unset):
            expire_after_filter = self.expire_after_filter.isoformat()

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
        if name_filter is not UNSET:
            field_dict["nameFilter"] = name_filter
        if created_after_filter is not UNSET:
            field_dict["createdAfterFilter"] = created_after_filter
        if created_before_filter is not UNSET:
            field_dict["createdBeforeFilter"] = created_before_filter
        if processed_after_filter is not UNSET:
            field_dict["processedAfterFilter"] = processed_after_filter
        if processed_before_filter is not UNSET:
            field_dict["processedBeforeFilter"] = processed_before_filter
        if state_filter is not UNSET:
            field_dict["stateFilter"] = state_filter
        if created_by_filter is not UNSET:
            field_dict["createdByFilter"] = created_by_filter
        if processed_by_filter is not UNSET:
            field_dict["processedByFilter"] = processed_by_filter
        if expire_before_filter is not UNSET:
            field_dict["expireBeforeFilter"] = expire_before_filter
        if expire_after_filter is not UNSET:
            field_dict["expireAfterFilter"] = expire_after_filter

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        skip = d.pop("skip", UNSET)

        limit = d.pop("limit", UNSET)

        _order_column = d.pop("orderColumn", UNSET)
        order_column: Union[Unset, EAuthorizationEventsFiltersOrderColumn]
        if isinstance(_order_column, Unset):
            order_column = UNSET
        else:
            order_column = EAuthorizationEventsFiltersOrderColumn(_order_column)

        order_asc = d.pop("orderAsc", UNSET)

        name_filter = d.pop("nameFilter", UNSET)

        _created_after_filter = d.pop("createdAfterFilter", UNSET)
        created_after_filter: Union[Unset, datetime.datetime]
        if isinstance(_created_after_filter, Unset):
            created_after_filter = UNSET
        else:
            created_after_filter = isoparse(_created_after_filter)

        _created_before_filter = d.pop("createdBeforeFilter", UNSET)
        created_before_filter: Union[Unset, datetime.datetime]
        if isinstance(_created_before_filter, Unset):
            created_before_filter = UNSET
        else:
            created_before_filter = isoparse(_created_before_filter)

        _processed_after_filter = d.pop("processedAfterFilter", UNSET)
        processed_after_filter: Union[Unset, datetime.datetime]
        if isinstance(_processed_after_filter, Unset):
            processed_after_filter = UNSET
        else:
            processed_after_filter = isoparse(_processed_after_filter)

        _processed_before_filter = d.pop("processedBeforeFilter", UNSET)
        processed_before_filter: Union[Unset, datetime.datetime]
        if isinstance(_processed_before_filter, Unset):
            processed_before_filter = UNSET
        else:
            processed_before_filter = isoparse(_processed_before_filter)

        _state_filter = d.pop("stateFilter", UNSET)
        state_filter: Union[Unset, EAuthorizationEventState]
        if isinstance(_state_filter, Unset):
            state_filter = UNSET
        else:
            state_filter = EAuthorizationEventState(_state_filter)

        created_by_filter = d.pop("createdByFilter", UNSET)

        processed_by_filter = d.pop("processedByFilter", UNSET)

        _expire_before_filter = d.pop("expireBeforeFilter", UNSET)
        expire_before_filter: Union[Unset, datetime.datetime]
        if isinstance(_expire_before_filter, Unset):
            expire_before_filter = UNSET
        else:
            expire_before_filter = isoparse(_expire_before_filter)

        _expire_after_filter = d.pop("expireAfterFilter", UNSET)
        expire_after_filter: Union[Unset, datetime.datetime]
        if isinstance(_expire_after_filter, Unset):
            expire_after_filter = UNSET
        else:
            expire_after_filter = isoparse(_expire_after_filter)

        authorization_events_filters = cls(
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            created_after_filter=created_after_filter,
            created_before_filter=created_before_filter,
            processed_after_filter=processed_after_filter,
            processed_before_filter=processed_before_filter,
            state_filter=state_filter,
            created_by_filter=created_by_filter,
            processed_by_filter=processed_by_filter,
            expire_before_filter=expire_before_filter,
            expire_after_filter=expire_after_filter,
        )

        authorization_events_filters.additional_properties = d
        return authorization_events_filters

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
