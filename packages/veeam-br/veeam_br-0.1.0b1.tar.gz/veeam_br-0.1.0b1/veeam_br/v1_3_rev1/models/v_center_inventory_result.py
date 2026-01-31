from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.agent_object_model import AgentObjectModel
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.hyper_v_object_model import HyperVObjectModel
    from ..models.pagination_result import PaginationResult
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="VCenterInventoryResult")


@_attrs_define
class VCenterInventoryResult:
    """Details on VMware vSphere objects.

    Attributes:
        data (list[Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel', 'VmwareObjectModel']]):
            Array of VMware vSphere objects.
        pagination (PaginationResult): Pagination settings.
    """

    data: list[Union["AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel"]]
    pagination: "PaginationResult"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        data = []
        for data_item_data in self.data:
            data_item: dict[str, Any]
            if isinstance(data_item_data, VmwareObjectModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, CloudDirectorObjectModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, HyperVObjectModel):
                data_item = data_item_data.to_dict()
            else:
                data_item = data_item_data.to_dict()

            data.append(data_item)

        pagination = self.pagination.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
                "pagination": pagination,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_object_model import AgentObjectModel
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.pagination_result import PaginationResult
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)
        data = []
        _data = d.pop("data")
        for data_item_data in _data:

            def _parse_data_item(
                data: object,
            ) -> Union["AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel"]:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_inventory_object_model_type_0 = VmwareObjectModel.from_dict(data)

                    return componentsschemas_inventory_object_model_type_0
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_inventory_object_model_type_1 = CloudDirectorObjectModel.from_dict(data)

                    return componentsschemas_inventory_object_model_type_1
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_inventory_object_model_type_2 = HyperVObjectModel.from_dict(data)

                    return componentsschemas_inventory_object_model_type_2
                except:  # noqa: E722
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_inventory_object_model_type_3 = AgentObjectModel.from_dict(data)

                return componentsschemas_inventory_object_model_type_3

            data_item = _parse_data_item(data_item_data)

            data.append(data_item)

        pagination = PaginationResult.from_dict(d.pop("pagination"))

        v_center_inventory_result = cls(
            data=data,
            pagination=pagination,
        )

        v_center_inventory_result.additional_properties = d
        return v_center_inventory_result

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
