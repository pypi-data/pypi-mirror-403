from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="RestoreTargetNetworkSpec")


@_attrs_define
class RestoreTargetNetworkSpec:
    """Network that the restored VM will be connected to. To get a network object, use the [Get Inventory
    Objects](#tag/Inventory-Browser/operation/GetInventoryObjects) request.

        Attributes:
            network (Union['CloudDirectorObjectModel', 'VmwareObjectModel']): Inventory object properties.
            disconnected (Union[Unset, bool]): If `true`, the restored VMs is not connected to any virtual network.
    """

    network: Union["CloudDirectorObjectModel", "VmwareObjectModel"]
    disconnected: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.vmware_object_model import VmwareObjectModel

        network: dict[str, Any]
        if isinstance(self.network, VmwareObjectModel):
            network = self.network.to_dict()
        else:
            network = self.network.to_dict()

        disconnected = self.disconnected

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "network": network,
            }
        )
        if disconnected is not UNSET:
            field_dict["disconnected"] = disconnected

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)

        def _parse_network(data: object) -> Union["CloudDirectorObjectModel", "VmwareObjectModel"]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_inventory_object_model_type_0 = VmwareObjectModel.from_dict(data)

                return componentsschemas_inventory_object_model_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_inventory_object_model_type_1 = CloudDirectorObjectModel.from_dict(data)

            return componentsschemas_inventory_object_model_type_1

        network = _parse_network(d.pop("network"))

        disconnected = d.pop("disconnected", UNSET)

        restore_target_network_spec = cls(
            network=network,
            disconnected=disconnected,
        )

        restore_target_network_spec.additional_properties = d
        return restore_target_network_spec

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
