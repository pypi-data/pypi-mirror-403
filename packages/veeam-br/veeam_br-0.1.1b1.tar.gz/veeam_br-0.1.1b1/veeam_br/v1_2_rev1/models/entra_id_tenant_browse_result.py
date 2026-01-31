from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.entra_id_tenant_admin_unit_browse_model import EntraIdTenantAdminUnitBrowseModel
    from ..models.entra_id_tenant_application_browse_model import EntraIdTenantApplicationBrowseModel
    from ..models.entra_id_tenant_conditional_access_policy_browse_model import (
        EntraIdTenantConditionalAccessPolicyBrowseModel,
    )
    from ..models.entra_id_tenant_group_browse_model import EntraIdTenantGroupBrowseModel
    from ..models.entra_id_tenant_role_browse_model import EntraIdTenantRoleBrowseModel
    from ..models.entra_id_tenant_user_browse_model import EntraIdTenantUserBrowseModel
    from ..models.pagination_result import PaginationResult


T = TypeVar("T", bound="EntraIdTenantBrowseResult")


@_attrs_define
class EntraIdTenantBrowseResult:
    """
    Attributes:
        data (list[Union['EntraIdTenantAdminUnitBrowseModel', 'EntraIdTenantApplicationBrowseModel',
            'EntraIdTenantConditionalAccessPolicyBrowseModel', 'EntraIdTenantGroupBrowseModel',
            'EntraIdTenantRoleBrowseModel', 'EntraIdTenantUserBrowseModel']]): Array of Microsoft Entra ID items.
        pagination (PaginationResult): Pagination settings.
    """

    data: list[
        Union[
            "EntraIdTenantAdminUnitBrowseModel",
            "EntraIdTenantApplicationBrowseModel",
            "EntraIdTenantConditionalAccessPolicyBrowseModel",
            "EntraIdTenantGroupBrowseModel",
            "EntraIdTenantRoleBrowseModel",
            "EntraIdTenantUserBrowseModel",
        ]
    ]
    pagination: "PaginationResult"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.entra_id_tenant_admin_unit_browse_model import EntraIdTenantAdminUnitBrowseModel
        from ..models.entra_id_tenant_application_browse_model import EntraIdTenantApplicationBrowseModel
        from ..models.entra_id_tenant_group_browse_model import EntraIdTenantGroupBrowseModel
        from ..models.entra_id_tenant_role_browse_model import EntraIdTenantRoleBrowseModel
        from ..models.entra_id_tenant_user_browse_model import EntraIdTenantUserBrowseModel

        data = []
        for data_item_data in self.data:
            data_item: dict[str, Any]
            if isinstance(data_item_data, EntraIdTenantUserBrowseModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, EntraIdTenantGroupBrowseModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, EntraIdTenantAdminUnitBrowseModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, EntraIdTenantRoleBrowseModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, EntraIdTenantApplicationBrowseModel):
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
        from ..models.entra_id_tenant_admin_unit_browse_model import EntraIdTenantAdminUnitBrowseModel
        from ..models.entra_id_tenant_application_browse_model import EntraIdTenantApplicationBrowseModel
        from ..models.entra_id_tenant_conditional_access_policy_browse_model import (
            EntraIdTenantConditionalAccessPolicyBrowseModel,
        )
        from ..models.entra_id_tenant_group_browse_model import EntraIdTenantGroupBrowseModel
        from ..models.entra_id_tenant_role_browse_model import EntraIdTenantRoleBrowseModel
        from ..models.entra_id_tenant_user_browse_model import EntraIdTenantUserBrowseModel
        from ..models.pagination_result import PaginationResult

        d = dict(src_dict)
        data = []
        _data = d.pop("data")
        for data_item_data in _data:

            def _parse_data_item(
                data: object,
            ) -> Union[
                "EntraIdTenantAdminUnitBrowseModel",
                "EntraIdTenantApplicationBrowseModel",
                "EntraIdTenantConditionalAccessPolicyBrowseModel",
                "EntraIdTenantGroupBrowseModel",
                "EntraIdTenantRoleBrowseModel",
                "EntraIdTenantUserBrowseModel",
            ]:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_entra_id_tenant_browse_model_type_0 = EntraIdTenantUserBrowseModel.from_dict(data)

                    return componentsschemas_entra_id_tenant_browse_model_type_0
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_entra_id_tenant_browse_model_type_1 = EntraIdTenantGroupBrowseModel.from_dict(
                        data
                    )

                    return componentsschemas_entra_id_tenant_browse_model_type_1
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_entra_id_tenant_browse_model_type_2 = EntraIdTenantAdminUnitBrowseModel.from_dict(
                        data
                    )

                    return componentsschemas_entra_id_tenant_browse_model_type_2
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_entra_id_tenant_browse_model_type_3 = EntraIdTenantRoleBrowseModel.from_dict(data)

                    return componentsschemas_entra_id_tenant_browse_model_type_3
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_entra_id_tenant_browse_model_type_4 = (
                        EntraIdTenantApplicationBrowseModel.from_dict(data)
                    )

                    return componentsschemas_entra_id_tenant_browse_model_type_4
                except:  # noqa: E722
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_entra_id_tenant_browse_model_type_5 = (
                    EntraIdTenantConditionalAccessPolicyBrowseModel.from_dict(data)
                )

                return componentsschemas_entra_id_tenant_browse_model_type_5

            data_item = _parse_data_item(data_item_data)

            data.append(data_item)

        pagination = PaginationResult.from_dict(d.pop("pagination"))

        entra_id_tenant_browse_result = cls(
            data=data,
            pagination=pagination,
        )

        entra_id_tenant_browse_result.additional_properties = d
        return entra_id_tenant_browse_result

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
