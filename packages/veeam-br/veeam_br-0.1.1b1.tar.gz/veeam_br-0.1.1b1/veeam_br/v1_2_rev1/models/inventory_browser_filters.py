from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.group_expression_model import GroupExpressionModel
    from ..models.pagination_filter import PaginationFilter
    from ..models.predicate_expression_model import PredicateExpressionModel
    from ..models.sort_expression_model import SortExpressionModel


T = TypeVar("T", bound="InventoryBrowserFilters")


@_attrs_define
class InventoryBrowserFilters:
    """
    Attributes:
        pagination (Union[Unset, PaginationFilter]): Pagination settings.
        filter_ (Union['GroupExpressionModel', 'PredicateExpressionModel', Unset]): Filter settings.
        sorting (Union[Unset, SortExpressionModel]): Sorting settings.
        hierarchy_type (Union[Unset, str]): Hierarchy type. Possible values&#58; <ul> <li>For VMware VSphere&#58;
            *HostsAndClusters*, *DatastoresAndVms*, *HostsAndDatastores*, *VmsAndTemplates*, *VmsAndTags*, *Network*</li>
            <li>For VMware Cloud Director&#58; *VAppsAndVms*, *Network*, *StoragePolicies*, *Datastores*</li></ul>
    """

    pagination: Union[Unset, "PaginationFilter"] = UNSET
    filter_: Union["GroupExpressionModel", "PredicateExpressionModel", Unset] = UNSET
    sorting: Union[Unset, "SortExpressionModel"] = UNSET
    hierarchy_type: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.predicate_expression_model import PredicateExpressionModel

        pagination: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.pagination, Unset):
            pagination = self.pagination.to_dict()

        filter_: Union[Unset, dict[str, Any]]
        if isinstance(self.filter_, Unset):
            filter_ = UNSET
        elif isinstance(self.filter_, PredicateExpressionModel):
            filter_ = self.filter_.to_dict()
        else:
            filter_ = self.filter_.to_dict()

        sorting: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.sorting, Unset):
            sorting = self.sorting.to_dict()

        hierarchy_type = self.hierarchy_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if pagination is not UNSET:
            field_dict["pagination"] = pagination
        if filter_ is not UNSET:
            field_dict["filter"] = filter_
        if sorting is not UNSET:
            field_dict["sorting"] = sorting
        if hierarchy_type is not UNSET:
            field_dict["hierarchyType"] = hierarchy_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.group_expression_model import GroupExpressionModel
        from ..models.pagination_filter import PaginationFilter
        from ..models.predicate_expression_model import PredicateExpressionModel
        from ..models.sort_expression_model import SortExpressionModel

        d = dict(src_dict)
        _pagination = d.pop("pagination", UNSET)
        pagination: Union[Unset, PaginationFilter]
        if isinstance(_pagination, Unset):
            pagination = UNSET
        else:
            pagination = PaginationFilter.from_dict(_pagination)

        def _parse_filter_(data: object) -> Union["GroupExpressionModel", "PredicateExpressionModel", Unset]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_filter_expression_model_type_0 = PredicateExpressionModel.from_dict(data)

                return componentsschemas_filter_expression_model_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_filter_expression_model_type_1 = GroupExpressionModel.from_dict(data)

            return componentsschemas_filter_expression_model_type_1

        filter_ = _parse_filter_(d.pop("filter", UNSET))

        _sorting = d.pop("sorting", UNSET)
        sorting: Union[Unset, SortExpressionModel]
        if isinstance(_sorting, Unset):
            sorting = UNSET
        else:
            sorting = SortExpressionModel.from_dict(_sorting)

        hierarchy_type = d.pop("hierarchyType", UNSET)

        inventory_browser_filters = cls(
            pagination=pagination,
            filter_=filter_,
            sorting=sorting,
            hierarchy_type=hierarchy_type,
        )

        inventory_browser_filters.additional_properties = d
        return inventory_browser_filters

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
