from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_flr_item_state_type import EFlrItemStateType
from ..models.e_flr_item_type import EFlrItemType
from ..types import UNSET, Unset

T = TypeVar("T", bound="FlrBrowseFiltrationModel")


@_attrs_define
class FlrBrowseFiltrationModel:
    """Filter settings.

    Attributes:
        item_states (Union[Unset, list[EFlrItemStateType]]): Filters items by their states.
        item_types (Union[Unset, list[EFlrItemType]]): Filters items by their types.
    """

    item_states: Union[Unset, list[EFlrItemStateType]] = UNSET
    item_types: Union[Unset, list[EFlrItemType]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        item_states: Union[Unset, list[str]] = UNSET
        if not isinstance(self.item_states, Unset):
            item_states = []
            for item_states_item_data in self.item_states:
                item_states_item = item_states_item_data.value
                item_states.append(item_states_item)

        item_types: Union[Unset, list[str]] = UNSET
        if not isinstance(self.item_types, Unset):
            item_types = []
            for item_types_item_data in self.item_types:
                item_types_item = item_types_item_data.value
                item_types.append(item_types_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if item_states is not UNSET:
            field_dict["itemStates"] = item_states
        if item_types is not UNSET:
            field_dict["itemTypes"] = item_types

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        item_states = []
        _item_states = d.pop("itemStates", UNSET)
        for item_states_item_data in _item_states or []:
            item_states_item = EFlrItemStateType(item_states_item_data)

            item_states.append(item_states_item)

        item_types = []
        _item_types = d.pop("itemTypes", UNSET)
        for item_types_item_data in _item_types or []:
            item_types_item = EFlrItemType(item_types_item_data)

            item_types.append(item_types_item)

        flr_browse_filtration_model = cls(
            item_states=item_states,
            item_types=item_types,
        )

        flr_browse_filtration_model.additional_properties = d
        return flr_browse_filtration_model

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
