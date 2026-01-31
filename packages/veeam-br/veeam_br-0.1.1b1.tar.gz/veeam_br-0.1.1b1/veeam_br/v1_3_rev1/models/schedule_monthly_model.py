from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_day_number_in_month import EDayNumberInMonth
from ..models.e_day_of_week import EDayOfWeek
from ..models.e_month import EMonth
from ..types import UNSET, Unset

T = TypeVar("T", bound="ScheduleMonthlyModel")


@_attrs_define
class ScheduleMonthlyModel:
    """Monthly scheduling options.

    Attributes:
        is_enabled (bool): If `true`, monthly schedule is enabled. Default: False.
        local_time (Union[Unset, str]): Local time when the job must start.
        day_of_week (Union[Unset, EDayOfWeek]): Day of the week.
        day_number_in_month (Union[Unset, EDayNumberInMonth]): Weekday number in the month.
        day_of_month (Union[Unset, int]): Day of the month when the job must start.
        months (Union[Unset, list[EMonth]]): Months when the job must start.
        is_last_day_of_month (Union[Unset, bool]): If `true`, the job will be scheduled for the last day of the month.
            This property overrides the `dayOfMonth` property.
    """

    is_enabled: bool = False
    local_time: Union[Unset, str] = UNSET
    day_of_week: Union[Unset, EDayOfWeek] = UNSET
    day_number_in_month: Union[Unset, EDayNumberInMonth] = UNSET
    day_of_month: Union[Unset, int] = UNSET
    months: Union[Unset, list[EMonth]] = UNSET
    is_last_day_of_month: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_enabled = self.is_enabled

        local_time = self.local_time

        day_of_week: Union[Unset, str] = UNSET
        if not isinstance(self.day_of_week, Unset):
            day_of_week = self.day_of_week.value

        day_number_in_month: Union[Unset, str] = UNSET
        if not isinstance(self.day_number_in_month, Unset):
            day_number_in_month = self.day_number_in_month.value

        day_of_month = self.day_of_month

        months: Union[Unset, list[str]] = UNSET
        if not isinstance(self.months, Unset):
            months = []
            for months_item_data in self.months:
                months_item = months_item_data.value
                months.append(months_item)

        is_last_day_of_month = self.is_last_day_of_month

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isEnabled": is_enabled,
            }
        )
        if local_time is not UNSET:
            field_dict["localTime"] = local_time
        if day_of_week is not UNSET:
            field_dict["dayOfWeek"] = day_of_week
        if day_number_in_month is not UNSET:
            field_dict["dayNumberInMonth"] = day_number_in_month
        if day_of_month is not UNSET:
            field_dict["dayOfMonth"] = day_of_month
        if months is not UNSET:
            field_dict["months"] = months
        if is_last_day_of_month is not UNSET:
            field_dict["isLastDayOfMonth"] = is_last_day_of_month

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_enabled = d.pop("isEnabled")

        local_time = d.pop("localTime", UNSET)

        _day_of_week = d.pop("dayOfWeek", UNSET)
        day_of_week: Union[Unset, EDayOfWeek]
        if isinstance(_day_of_week, Unset):
            day_of_week = UNSET
        else:
            day_of_week = EDayOfWeek(_day_of_week)

        _day_number_in_month = d.pop("dayNumberInMonth", UNSET)
        day_number_in_month: Union[Unset, EDayNumberInMonth]
        if isinstance(_day_number_in_month, Unset):
            day_number_in_month = UNSET
        else:
            day_number_in_month = EDayNumberInMonth(_day_number_in_month)

        day_of_month = d.pop("dayOfMonth", UNSET)

        months = []
        _months = d.pop("months", UNSET)
        for months_item_data in _months or []:
            months_item = EMonth(months_item_data)

            months.append(months_item)

        is_last_day_of_month = d.pop("isLastDayOfMonth", UNSET)

        schedule_monthly_model = cls(
            is_enabled=is_enabled,
            local_time=local_time,
            day_of_week=day_of_week,
            day_number_in_month=day_number_in_month,
            day_of_month=day_of_month,
            months=months,
            is_last_day_of_month=is_last_day_of_month,
        )

        schedule_monthly_model.additional_properties = d
        return schedule_monthly_model

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
