from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.preferred_networks_model import PreferredNetworksModel
    from ..models.traffic_rule_model import TrafficRuleModel


T = TypeVar("T", bound="GlobalNetworkTrafficRulesModel")


@_attrs_define
class GlobalNetworkTrafficRulesModel:
    """Global network traffic rules.

    Attributes:
        use_multiple_streams_per_job (bool): If `true`, Veeam Backup & Replication uses multiple TCP/IP transfer
            connection for every job session.
        upload_streams_count (Union[Unset, int]): Number of TCP/IP connections per job.
        traffic_rules (Union[Unset, list['TrafficRuleModel']]): Array of traffic rules.
        preferred_networks (Union[Unset, PreferredNetworksModel]): Preferred networks used for backup and replication
            traffic.
    """

    use_multiple_streams_per_job: bool
    upload_streams_count: Union[Unset, int] = UNSET
    traffic_rules: Union[Unset, list["TrafficRuleModel"]] = UNSET
    preferred_networks: Union[Unset, "PreferredNetworksModel"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        use_multiple_streams_per_job = self.use_multiple_streams_per_job

        upload_streams_count = self.upload_streams_count

        traffic_rules: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.traffic_rules, Unset):
            traffic_rules = []
            for traffic_rules_item_data in self.traffic_rules:
                traffic_rules_item = traffic_rules_item_data.to_dict()
                traffic_rules.append(traffic_rules_item)

        preferred_networks: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.preferred_networks, Unset):
            preferred_networks = self.preferred_networks.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "useMultipleStreamsPerJob": use_multiple_streams_per_job,
            }
        )
        if upload_streams_count is not UNSET:
            field_dict["uploadStreamsCount"] = upload_streams_count
        if traffic_rules is not UNSET:
            field_dict["trafficRules"] = traffic_rules
        if preferred_networks is not UNSET:
            field_dict["preferredNetworks"] = preferred_networks

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.preferred_networks_model import PreferredNetworksModel
        from ..models.traffic_rule_model import TrafficRuleModel

        d = dict(src_dict)
        use_multiple_streams_per_job = d.pop("useMultipleStreamsPerJob")

        upload_streams_count = d.pop("uploadStreamsCount", UNSET)

        traffic_rules = []
        _traffic_rules = d.pop("trafficRules", UNSET)
        for traffic_rules_item_data in _traffic_rules or []:
            traffic_rules_item = TrafficRuleModel.from_dict(traffic_rules_item_data)

            traffic_rules.append(traffic_rules_item)

        _preferred_networks = d.pop("preferredNetworks", UNSET)
        preferred_networks: Union[Unset, PreferredNetworksModel]
        if isinstance(_preferred_networks, Unset):
            preferred_networks = UNSET
        else:
            preferred_networks = PreferredNetworksModel.from_dict(_preferred_networks)

        global_network_traffic_rules_model = cls(
            use_multiple_streams_per_job=use_multiple_streams_per_job,
            upload_streams_count=upload_streams_count,
            traffic_rules=traffic_rules,
            preferred_networks=preferred_networks,
        )

        global_network_traffic_rules_model.additional_properties = d
        return global_network_traffic_rules_model

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
