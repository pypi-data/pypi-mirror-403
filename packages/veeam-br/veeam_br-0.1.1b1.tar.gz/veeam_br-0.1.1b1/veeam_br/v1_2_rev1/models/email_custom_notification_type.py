from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="EmailCustomNotificationType")


@_attrs_define
class EmailCustomNotificationType:
    """Custom notification settings.

    Attributes:
        subject (Union[Unset, str]): Notification subject. Use the following variables in the subject:<ul> <li>*%Time%*
            — completion time</li> <li>*%JobName%* — job name</li> <li>*%JobResult%* — job result</li> <li>*%ObjectCount%* —
            number of VMs in the job</li> <li>*%Issues%* — number of VMs in the job that have finished with the Warning or
            Failed status</li></ul>
        notify_on_success (Union[Unset, bool]): If `true`, email notifications are sent when the job completes
            successfully.
        notify_on_warning (Union[Unset, bool]): If `true`, email notifications are sent when the job completes with a
            warning.
        notify_on_error (Union[Unset, bool]): If `true`, email notifications are sent when the job fails.
        suppress_notification_until_last_retry (Union[Unset, bool]): If `true`, email notifications are sent about the
            final job status only (not per every job retry).
    """

    subject: Union[Unset, str] = UNSET
    notify_on_success: Union[Unset, bool] = UNSET
    notify_on_warning: Union[Unset, bool] = UNSET
    notify_on_error: Union[Unset, bool] = UNSET
    suppress_notification_until_last_retry: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        subject = self.subject

        notify_on_success = self.notify_on_success

        notify_on_warning = self.notify_on_warning

        notify_on_error = self.notify_on_error

        suppress_notification_until_last_retry = self.suppress_notification_until_last_retry

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if subject is not UNSET:
            field_dict["subject"] = subject
        if notify_on_success is not UNSET:
            field_dict["notifyOnSuccess"] = notify_on_success
        if notify_on_warning is not UNSET:
            field_dict["notifyOnWarning"] = notify_on_warning
        if notify_on_error is not UNSET:
            field_dict["notifyOnError"] = notify_on_error
        if suppress_notification_until_last_retry is not UNSET:
            field_dict["SuppressNotificationUntilLastRetry"] = suppress_notification_until_last_retry

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        subject = d.pop("subject", UNSET)

        notify_on_success = d.pop("notifyOnSuccess", UNSET)

        notify_on_warning = d.pop("notifyOnWarning", UNSET)

        notify_on_error = d.pop("notifyOnError", UNSET)

        suppress_notification_until_last_retry = d.pop("SuppressNotificationUntilLastRetry", UNSET)

        email_custom_notification_type = cls(
            subject=subject,
            notify_on_success=notify_on_success,
            notify_on_warning=notify_on_warning,
            notify_on_error=notify_on_error,
            suppress_notification_until_last_retry=suppress_notification_until_last_retry,
        )

        email_custom_notification_type.additional_properties = d
        return email_custom_notification_type

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
