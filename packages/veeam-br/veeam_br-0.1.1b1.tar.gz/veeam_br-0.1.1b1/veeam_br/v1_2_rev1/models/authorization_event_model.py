import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.e_authorization_event_state import EAuthorizationEventState
from ..types import UNSET, Unset

T = TypeVar("T", bound="AuthorizationEventModel")


@_attrs_define
class AuthorizationEventModel:
    """
    Attributes:
        id (Union[Unset, UUID]): Event ID.
        name (Union[Unset, str]): Event name.
        description (Union[Unset, str]): Event description.
        state (Union[Unset, EAuthorizationEventState]): Event state.
        creation_time (Union[Unset, datetime.datetime]): Date and time when the event was created.
        created_by (Union[Unset, str]): User initiated the event.
        expiration_time (Union[Unset, datetime.datetime]): Date and time when the event expires.
        processed_by (Union[Unset, str]): User processed the event.
        processed_time (Union[Unset, datetime.datetime]): Date and time when the event was processed.
    """

    id: Union[Unset, UUID] = UNSET
    name: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    state: Union[Unset, EAuthorizationEventState] = UNSET
    creation_time: Union[Unset, datetime.datetime] = UNSET
    created_by: Union[Unset, str] = UNSET
    expiration_time: Union[Unset, datetime.datetime] = UNSET
    processed_by: Union[Unset, str] = UNSET
    processed_time: Union[Unset, datetime.datetime] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: Union[Unset, str] = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        name = self.name

        description = self.description

        state: Union[Unset, str] = UNSET
        if not isinstance(self.state, Unset):
            state = self.state.value

        creation_time: Union[Unset, str] = UNSET
        if not isinstance(self.creation_time, Unset):
            creation_time = self.creation_time.isoformat()

        created_by = self.created_by

        expiration_time: Union[Unset, str] = UNSET
        if not isinstance(self.expiration_time, Unset):
            expiration_time = self.expiration_time.isoformat()

        processed_by = self.processed_by

        processed_time: Union[Unset, str] = UNSET
        if not isinstance(self.processed_time, Unset):
            processed_time = self.processed_time.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if state is not UNSET:
            field_dict["state"] = state
        if creation_time is not UNSET:
            field_dict["creationTime"] = creation_time
        if created_by is not UNSET:
            field_dict["createdBy"] = created_by
        if expiration_time is not UNSET:
            field_dict["expirationTime"] = expiration_time
        if processed_by is not UNSET:
            field_dict["processedBy"] = processed_by
        if processed_time is not UNSET:
            field_dict["processedTime"] = processed_time

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _id = d.pop("id", UNSET)
        id: Union[Unset, UUID]
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        name = d.pop("name", UNSET)

        description = d.pop("description", UNSET)

        _state = d.pop("state", UNSET)
        state: Union[Unset, EAuthorizationEventState]
        if isinstance(_state, Unset):
            state = UNSET
        else:
            state = EAuthorizationEventState(_state)

        _creation_time = d.pop("creationTime", UNSET)
        creation_time: Union[Unset, datetime.datetime]
        if isinstance(_creation_time, Unset):
            creation_time = UNSET
        else:
            creation_time = isoparse(_creation_time)

        created_by = d.pop("createdBy", UNSET)

        _expiration_time = d.pop("expirationTime", UNSET)
        expiration_time: Union[Unset, datetime.datetime]
        if isinstance(_expiration_time, Unset):
            expiration_time = UNSET
        else:
            expiration_time = isoparse(_expiration_time)

        processed_by = d.pop("processedBy", UNSET)

        _processed_time = d.pop("processedTime", UNSET)
        processed_time: Union[Unset, datetime.datetime]
        if isinstance(_processed_time, Unset):
            processed_time = UNSET
        else:
            processed_time = isoparse(_processed_time)

        authorization_event_model = cls(
            id=id,
            name=name,
            description=description,
            state=state,
            creation_time=creation_time,
            created_by=created_by,
            expiration_time=expiration_time,
            processed_by=processed_by,
            processed_time=processed_time,
        )

        authorization_event_model.additional_properties = d
        return authorization_event_model

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
