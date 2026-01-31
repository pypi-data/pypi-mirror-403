from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.wan_accelerator_cache_model import WANAcceleratorCacheModel
    from ..models.wan_accelerator_server_model import WANAcceleratorServerModel


T = TypeVar("T", bound="WANAcceleratorModel")


@_attrs_define
class WANAcceleratorModel:
    """
    Attributes:
        id (Union[Unset, UUID]): WAN accelerator ID.
        name (Union[Unset, str]): Server name or IP address.
        server (Union[Unset, WANAcceleratorServerModel]): Microsoft Windows server used as a WAN accelerator.
        cache (Union[Unset, WANAcceleratorCacheModel]): Cache settings. Cache is used for storing service files (for
            source and target WAN accelerators) and global cache data (for target WAN accelerator).
    """

    id: Union[Unset, UUID] = UNSET
    name: Union[Unset, str] = UNSET
    server: Union[Unset, "WANAcceleratorServerModel"] = UNSET
    cache: Union[Unset, "WANAcceleratorCacheModel"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: Union[Unset, str] = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        name = self.name

        server: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.server, Unset):
            server = self.server.to_dict()

        cache: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.cache, Unset):
            cache = self.cache.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if server is not UNSET:
            field_dict["server"] = server
        if cache is not UNSET:
            field_dict["cache"] = cache

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.wan_accelerator_cache_model import WANAcceleratorCacheModel
        from ..models.wan_accelerator_server_model import WANAcceleratorServerModel

        d = dict(src_dict)
        _id = d.pop("id", UNSET)
        id: Union[Unset, UUID]
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        name = d.pop("name", UNSET)

        _server = d.pop("server", UNSET)
        server: Union[Unset, WANAcceleratorServerModel]
        if isinstance(_server, Unset):
            server = UNSET
        else:
            server = WANAcceleratorServerModel.from_dict(_server)

        _cache = d.pop("cache", UNSET)
        cache: Union[Unset, WANAcceleratorCacheModel]
        if isinstance(_cache, Unset):
            cache = UNSET
        else:
            cache = WANAcceleratorCacheModel.from_dict(_cache)

        wan_accelerator_model = cls(
            id=id,
            name=name,
            server=server,
            cache=cache,
        )

        wan_accelerator_model.additional_properties = d
        return wan_accelerator_model

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
