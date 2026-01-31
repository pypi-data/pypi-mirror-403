from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.schedule_after_this_job_model import ScheduleAfterThisJobModel
    from ..models.schedule_backup_window_model import ScheduleBackupWindowModel
    from ..models.schedule_daily_model import ScheduleDailyModel
    from ..models.schedule_monthly_model import ScheduleMonthlyModel
    from ..models.schedule_periodically_model import SchedulePeriodicallyModel
    from ..models.schedule_retry_model import ScheduleRetryModel


T = TypeVar("T", bound="BackupScheduleModel")


@_attrs_define
class BackupScheduleModel:
    """Job scheduling options.

    Attributes:
        run_automatically (bool): If `true`, job scheduling is enabled. Default: False.
        daily (Union[Unset, ScheduleDailyModel]): Daily scheduling options.
        monthly (Union[Unset, ScheduleMonthlyModel]): Monthly scheduling options.
        periodically (Union[Unset, SchedulePeriodicallyModel]): Periodic scheduling options.
        continuously (Union[Unset, ScheduleBackupWindowModel]): Backup window settings.
        after_this_job (Union[Unset, ScheduleAfterThisJobModel]): Job chaining options.
        retry (Union[Unset, ScheduleRetryModel]): Retry options.
        backup_window (Union[Unset, ScheduleBackupWindowModel]): Backup window settings.
    """

    run_automatically: bool = False
    daily: Union[Unset, "ScheduleDailyModel"] = UNSET
    monthly: Union[Unset, "ScheduleMonthlyModel"] = UNSET
    periodically: Union[Unset, "SchedulePeriodicallyModel"] = UNSET
    continuously: Union[Unset, "ScheduleBackupWindowModel"] = UNSET
    after_this_job: Union[Unset, "ScheduleAfterThisJobModel"] = UNSET
    retry: Union[Unset, "ScheduleRetryModel"] = UNSET
    backup_window: Union[Unset, "ScheduleBackupWindowModel"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        run_automatically = self.run_automatically

        daily: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.daily, Unset):
            daily = self.daily.to_dict()

        monthly: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.monthly, Unset):
            monthly = self.monthly.to_dict()

        periodically: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.periodically, Unset):
            periodically = self.periodically.to_dict()

        continuously: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.continuously, Unset):
            continuously = self.continuously.to_dict()

        after_this_job: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.after_this_job, Unset):
            after_this_job = self.after_this_job.to_dict()

        retry: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.retry, Unset):
            retry = self.retry.to_dict()

        backup_window: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.backup_window, Unset):
            backup_window = self.backup_window.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "runAutomatically": run_automatically,
            }
        )
        if daily is not UNSET:
            field_dict["daily"] = daily
        if monthly is not UNSET:
            field_dict["monthly"] = monthly
        if periodically is not UNSET:
            field_dict["periodically"] = periodically
        if continuously is not UNSET:
            field_dict["continuously"] = continuously
        if after_this_job is not UNSET:
            field_dict["afterThisJob"] = after_this_job
        if retry is not UNSET:
            field_dict["retry"] = retry
        if backup_window is not UNSET:
            field_dict["backupWindow"] = backup_window

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.schedule_after_this_job_model import ScheduleAfterThisJobModel
        from ..models.schedule_backup_window_model import ScheduleBackupWindowModel
        from ..models.schedule_daily_model import ScheduleDailyModel
        from ..models.schedule_monthly_model import ScheduleMonthlyModel
        from ..models.schedule_periodically_model import SchedulePeriodicallyModel
        from ..models.schedule_retry_model import ScheduleRetryModel

        d = dict(src_dict)
        run_automatically = d.pop("runAutomatically")

        _daily = d.pop("daily", UNSET)
        daily: Union[Unset, ScheduleDailyModel]
        if isinstance(_daily, Unset):
            daily = UNSET
        else:
            daily = ScheduleDailyModel.from_dict(_daily)

        _monthly = d.pop("monthly", UNSET)
        monthly: Union[Unset, ScheduleMonthlyModel]
        if isinstance(_monthly, Unset):
            monthly = UNSET
        else:
            monthly = ScheduleMonthlyModel.from_dict(_monthly)

        _periodically = d.pop("periodically", UNSET)
        periodically: Union[Unset, SchedulePeriodicallyModel]
        if isinstance(_periodically, Unset):
            periodically = UNSET
        else:
            periodically = SchedulePeriodicallyModel.from_dict(_periodically)

        _continuously = d.pop("continuously", UNSET)
        continuously: Union[Unset, ScheduleBackupWindowModel]
        if isinstance(_continuously, Unset):
            continuously = UNSET
        else:
            continuously = ScheduleBackupWindowModel.from_dict(_continuously)

        _after_this_job = d.pop("afterThisJob", UNSET)
        after_this_job: Union[Unset, ScheduleAfterThisJobModel]
        if isinstance(_after_this_job, Unset):
            after_this_job = UNSET
        else:
            after_this_job = ScheduleAfterThisJobModel.from_dict(_after_this_job)

        _retry = d.pop("retry", UNSET)
        retry: Union[Unset, ScheduleRetryModel]
        if isinstance(_retry, Unset):
            retry = UNSET
        else:
            retry = ScheduleRetryModel.from_dict(_retry)

        _backup_window = d.pop("backupWindow", UNSET)
        backup_window: Union[Unset, ScheduleBackupWindowModel]
        if isinstance(_backup_window, Unset):
            backup_window = UNSET
        else:
            backup_window = ScheduleBackupWindowModel.from_dict(_backup_window)

        backup_schedule_model = cls(
            run_automatically=run_automatically,
            daily=daily,
            monthly=monthly,
            periodically=periodically,
            continuously=continuously,
            after_this_job=after_this_job,
            retry=retry,
            backup_window=backup_window,
        )

        backup_schedule_model.additional_properties = d
        return backup_schedule_model

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
