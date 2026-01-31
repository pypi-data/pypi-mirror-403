from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.agent_object_model import AgentObjectModel
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.hyper_v_object_model import HyperVObjectModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="EntireCloudDirectorVMRestoreLocationModel")


@_attrs_define
class EntireCloudDirectorVMRestoreLocationModel:
    """Target location settings. To get a vApp object, run the [Get Inventory Objects](Inventory-
    Browser#operation/GetInventoryObjects) request.

        Attributes:
            new_name (str): New VM name.
            v_app (Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel', 'VmwareObjectModel']):
                Inventory object properties.
            restore_v_sphere_vm_tags (bool): If `true`, VMware vSphere tags will be restored for this VM.
    """

    new_name: str
    v_app: Union["AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel"]
    restore_v_sphere_vm_tags: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        new_name = self.new_name

        v_app: dict[str, Any]
        if isinstance(self.v_app, VmwareObjectModel):
            v_app = self.v_app.to_dict()
        elif isinstance(self.v_app, CloudDirectorObjectModel):
            v_app = self.v_app.to_dict()
        elif isinstance(self.v_app, HyperVObjectModel):
            v_app = self.v_app.to_dict()
        else:
            v_app = self.v_app.to_dict()

        restore_v_sphere_vm_tags = self.restore_v_sphere_vm_tags

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "newName": new_name,
                "vApp": v_app,
                "restoreVSphereVMTags": restore_v_sphere_vm_tags,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_object_model import AgentObjectModel
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)
        new_name = d.pop("newName")

        def _parse_v_app(
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

        v_app = _parse_v_app(d.pop("vApp"))

        restore_v_sphere_vm_tags = d.pop("restoreVSphereVMTags")

        entire_cloud_director_vm_restore_location_model = cls(
            new_name=new_name,
            v_app=v_app,
            restore_v_sphere_vm_tags=restore_v_sphere_vm_tags,
        )

        entire_cloud_director_vm_restore_location_model.additional_properties = d
        return entire_cloud_director_vm_restore_location_model

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
