from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_application_settings_vss import EApplicationSettingsVSS
from ..models.e_transaction_logs_settings import ETransactionLogsSettings
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_object_model import AgentObjectModel
    from ..models.backup_fs_exclusions_model import BackupFSExclusionsModel
    from ..models.backup_oracle_settings_model import BackupOracleSettingsModel
    from ..models.backup_postgre_sql_settings_model import BackupPostgreSQLSettingsModel
    from ..models.backup_script_settings_model import BackupScriptSettingsModel
    from ..models.backup_sql_settings_model import BackupSQLSettingsModel
    from ..models.cloud_director_object_model import CloudDirectorObjectModel
    from ..models.hyper_v_object_model import HyperVObjectModel
    from ..models.vmware_object_model import VmwareObjectModel


T = TypeVar("T", bound="BackupApplicationSettingsModel")


@_attrs_define
class BackupApplicationSettingsModel:
    """Application backup settings.

    Attributes:
        vm_object (Union['AgentObjectModel', 'CloudDirectorObjectModel', 'HyperVObjectModel', 'VmwareObjectModel']):
            Inventory object properties.
        vss (EApplicationSettingsVSS): Behavior scenario for application-aware processing.
        use_persistent_guest_agent (Union[Unset, bool]): If `true`, persistent guest agent is used.
        transaction_logs (Union[Unset, ETransactionLogsSettings]): Transaction logs settings that define whether copy-
            only backups must be created, or transaction logs for Microsoft Exchange, Microsoft SQL and Oracle VMs must be
            processed.<p> If transaction log processing is selected, specify the following parameters:<ul> <li>[For
            Microsoft SQL Server VMs] Microsoft SQL Server transaction log settings</li> <li>[For Oracle VMs] Oracle
            archived log settings</li></ul>
        sql (Union[Unset, BackupSQLSettingsModel]): Microsoft SQL Server transaction log settings.
        oracle (Union[Unset, BackupOracleSettingsModel]): Oracle archived log settings.
        postgre_sql (Union[Unset, BackupPostgreSQLSettingsModel]): PostgreSQL WAL files settings.
        exclusions (Union[Unset, BackupFSExclusionsModel]): VM guest OS file exclusion.
        scripts (Union[Unset, BackupScriptSettingsModel]): Pre-freeze and post-thaw scripts.
    """

    vm_object: Union["AgentObjectModel", "CloudDirectorObjectModel", "HyperVObjectModel", "VmwareObjectModel"]
    vss: EApplicationSettingsVSS
    use_persistent_guest_agent: Union[Unset, bool] = UNSET
    transaction_logs: Union[Unset, ETransactionLogsSettings] = UNSET
    sql: Union[Unset, "BackupSQLSettingsModel"] = UNSET
    oracle: Union[Unset, "BackupOracleSettingsModel"] = UNSET
    postgre_sql: Union[Unset, "BackupPostgreSQLSettingsModel"] = UNSET
    exclusions: Union[Unset, "BackupFSExclusionsModel"] = UNSET
    scripts: Union[Unset, "BackupScriptSettingsModel"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        vm_object: dict[str, Any]
        if isinstance(self.vm_object, VmwareObjectModel):
            vm_object = self.vm_object.to_dict()
        elif isinstance(self.vm_object, CloudDirectorObjectModel):
            vm_object = self.vm_object.to_dict()
        elif isinstance(self.vm_object, HyperVObjectModel):
            vm_object = self.vm_object.to_dict()
        else:
            vm_object = self.vm_object.to_dict()

        vss = self.vss.value

        use_persistent_guest_agent = self.use_persistent_guest_agent

        transaction_logs: Union[Unset, str] = UNSET
        if not isinstance(self.transaction_logs, Unset):
            transaction_logs = self.transaction_logs.value

        sql: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.sql, Unset):
            sql = self.sql.to_dict()

        oracle: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.oracle, Unset):
            oracle = self.oracle.to_dict()

        postgre_sql: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.postgre_sql, Unset):
            postgre_sql = self.postgre_sql.to_dict()

        exclusions: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.exclusions, Unset):
            exclusions = self.exclusions.to_dict()

        scripts: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.scripts, Unset):
            scripts = self.scripts.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "vmObject": vm_object,
                "vss": vss,
            }
        )
        if use_persistent_guest_agent is not UNSET:
            field_dict["usePersistentGuestAgent"] = use_persistent_guest_agent
        if transaction_logs is not UNSET:
            field_dict["transactionLogs"] = transaction_logs
        if sql is not UNSET:
            field_dict["sql"] = sql
        if oracle is not UNSET:
            field_dict["oracle"] = oracle
        if postgre_sql is not UNSET:
            field_dict["postgreSQL"] = postgre_sql
        if exclusions is not UNSET:
            field_dict["exclusions"] = exclusions
        if scripts is not UNSET:
            field_dict["scripts"] = scripts

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_object_model import AgentObjectModel
        from ..models.backup_fs_exclusions_model import BackupFSExclusionsModel
        from ..models.backup_oracle_settings_model import BackupOracleSettingsModel
        from ..models.backup_postgre_sql_settings_model import BackupPostgreSQLSettingsModel
        from ..models.backup_script_settings_model import BackupScriptSettingsModel
        from ..models.backup_sql_settings_model import BackupSQLSettingsModel
        from ..models.cloud_director_object_model import CloudDirectorObjectModel
        from ..models.hyper_v_object_model import HyperVObjectModel
        from ..models.vmware_object_model import VmwareObjectModel

        d = dict(src_dict)

        def _parse_vm_object(
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

        vm_object = _parse_vm_object(d.pop("vmObject"))

        vss = EApplicationSettingsVSS(d.pop("vss"))

        use_persistent_guest_agent = d.pop("usePersistentGuestAgent", UNSET)

        _transaction_logs = d.pop("transactionLogs", UNSET)
        transaction_logs: Union[Unset, ETransactionLogsSettings]
        if isinstance(_transaction_logs, Unset):
            transaction_logs = UNSET
        else:
            transaction_logs = ETransactionLogsSettings(_transaction_logs)

        _sql = d.pop("sql", UNSET)
        sql: Union[Unset, BackupSQLSettingsModel]
        if isinstance(_sql, Unset):
            sql = UNSET
        else:
            sql = BackupSQLSettingsModel.from_dict(_sql)

        _oracle = d.pop("oracle", UNSET)
        oracle: Union[Unset, BackupOracleSettingsModel]
        if isinstance(_oracle, Unset):
            oracle = UNSET
        else:
            oracle = BackupOracleSettingsModel.from_dict(_oracle)

        _postgre_sql = d.pop("postgreSQL", UNSET)
        postgre_sql: Union[Unset, BackupPostgreSQLSettingsModel]
        if isinstance(_postgre_sql, Unset):
            postgre_sql = UNSET
        else:
            postgre_sql = BackupPostgreSQLSettingsModel.from_dict(_postgre_sql)

        _exclusions = d.pop("exclusions", UNSET)
        exclusions: Union[Unset, BackupFSExclusionsModel]
        if isinstance(_exclusions, Unset):
            exclusions = UNSET
        else:
            exclusions = BackupFSExclusionsModel.from_dict(_exclusions)

        _scripts = d.pop("scripts", UNSET)
        scripts: Union[Unset, BackupScriptSettingsModel]
        if isinstance(_scripts, Unset):
            scripts = UNSET
        else:
            scripts = BackupScriptSettingsModel.from_dict(_scripts)

        backup_application_settings_model = cls(
            vm_object=vm_object,
            vss=vss,
            use_persistent_guest_agent=use_persistent_guest_agent,
            transaction_logs=transaction_logs,
            sql=sql,
            oracle=oracle,
            postgre_sql=postgre_sql,
            exclusions=exclusions,
            scripts=scripts,
        )

        backup_application_settings_model.additional_properties = d
        return backup_application_settings_model

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
