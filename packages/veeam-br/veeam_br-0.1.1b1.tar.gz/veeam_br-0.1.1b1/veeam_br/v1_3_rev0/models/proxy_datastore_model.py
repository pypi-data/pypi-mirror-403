from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_object_model import AgentObjectModel
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.hyper_v_object_model import HyperVObjectModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="ProxyDatastoreModel")


@_attrs_define
class ProxyDatastoreModel:
    """Datastore to which the backup proxy has a direct SAN or NFS connection.

    Attributes:
        datastore (Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel', 'VmwareObjectModel',
            Unset]): Inventory object properties.
        vm_count (Union[Unset, int]): Number of VMs.
    """

    datastore: Union[
        "AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel", Unset
    ] = UNSET
    vm_count: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        datastore: Union[Unset, dict[str, Any]]
        if isinstance(self.datastore, Unset):
            datastore = UNSET
        elif isinstance(self.datastore, VmwareObjectModel):
            datastore = self.datastore.to_dict()
        elif isinstance(self.datastore, CloudDirectorObjectModel):
            datastore = self.datastore.to_dict()
        elif isinstance(self.datastore, HyperVObjectModel):
            datastore = self.datastore.to_dict()
        else:
            datastore = self.datastore.to_dict()

        vm_count = self.vm_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if datastore is not UNSET:
            field_dict["datastore"] = datastore
        if vm_count is not UNSET:
            field_dict["vmCount"] = vm_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_object_model import AgentObjectModel
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)

        def _parse_datastore(
            data: object,
        ) -> Union["AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel", Unset]:
            if isinstance(data, Unset):
                return data
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

        datastore = _parse_datastore(d.pop("datastore", UNSET))

        vm_count = d.pop("vmCount", UNSET)

        proxy_datastore_model = cls(
            datastore=datastore,
            vm_count=vm_count,
        )

        proxy_datastore_model.additional_properties = d
        return proxy_datastore_model

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
