from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.general_options_email_notifications_model import GeneralOptionsEmailNotificationsModel
    from ..models.general_options_notifications_model import GeneralOptionsNotificationsModel
    from ..models.general_options_siem_integration_model import GeneralOptionsSiemIntegrationModel


T = TypeVar("T", bound="GeneralOptionsModel")


@_attrs_define
class GeneralOptionsModel:
    """Veeam Backup & Replication settings.

    Attributes:
        email_settings (Union[Unset, GeneralOptionsEmailNotificationsModel]): Global email notification settings and job
            notifications.
        notifications (Union[Unset, GeneralOptionsNotificationsModel]): Other notifications such as notifications on low
            disk space, support contract expiration, and available updates.
        siem_integration (Union[Unset, GeneralOptionsSiemIntegrationModel]): SIEM integration settings.
    """

    email_settings: Union[Unset, "GeneralOptionsEmailNotificationsModel"] = UNSET
    notifications: Union[Unset, "GeneralOptionsNotificationsModel"] = UNSET
    siem_integration: Union[Unset, "GeneralOptionsSiemIntegrationModel"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        email_settings: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.email_settings, Unset):
            email_settings = self.email_settings.to_dict()

        notifications: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.notifications, Unset):
            notifications = self.notifications.to_dict()

        siem_integration: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.siem_integration, Unset):
            siem_integration = self.siem_integration.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if email_settings is not UNSET:
            field_dict["emailSettings"] = email_settings
        if notifications is not UNSET:
            field_dict["notifications"] = notifications
        if siem_integration is not UNSET:
            field_dict["siemIntegration"] = siem_integration

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.general_options_email_notifications_model import GeneralOptionsEmailNotificationsModel
        from ..models.general_options_notifications_model import GeneralOptionsNotificationsModel
        from ..models.general_options_siem_integration_model import GeneralOptionsSiemIntegrationModel

        d = dict(src_dict)
        _email_settings = d.pop("emailSettings", UNSET)
        email_settings: Union[Unset, GeneralOptionsEmailNotificationsModel]
        if isinstance(_email_settings, Unset):
            email_settings = UNSET
        else:
            email_settings = GeneralOptionsEmailNotificationsModel.from_dict(_email_settings)

        _notifications = d.pop("notifications", UNSET)
        notifications: Union[Unset, GeneralOptionsNotificationsModel]
        if isinstance(_notifications, Unset):
            notifications = UNSET
        else:
            notifications = GeneralOptionsNotificationsModel.from_dict(_notifications)

        _siem_integration = d.pop("siemIntegration", UNSET)
        siem_integration: Union[Unset, GeneralOptionsSiemIntegrationModel]
        if isinstance(_siem_integration, Unset):
            siem_integration = UNSET
        else:
            siem_integration = GeneralOptionsSiemIntegrationModel.from_dict(_siem_integration)

        general_options_model = cls(
            email_settings=email_settings,
            notifications=notifications,
            siem_integration=siem_integration,
        )

        general_options_model.additional_properties = d
        return general_options_model

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
