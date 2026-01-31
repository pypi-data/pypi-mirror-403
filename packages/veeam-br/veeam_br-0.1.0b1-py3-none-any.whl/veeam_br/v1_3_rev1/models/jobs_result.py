from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.backup_copy_job_model import BackupCopyJobModel
    from ..models.backup_job_model import BackupJobModel
    from ..models.cloud_director_backup_job_model import CloudDirectorBackupJobModel
    from ..models.entra_id_audit_log_backup_job_model import EntraIDAuditLogBackupJobModel
    from ..models.entra_id_tenant_backup_copy_job_model import EntraIDTenantBackupCopyJobModel
    from ..models.entra_id_tenant_backup_job_model import EntraIDTenantBackupJobModel
    from ..models.file_backup_copy_job_model import FileBackupCopyJobModel
    from ..models.file_backup_job_model import FileBackupJobModel
    from ..models.hyper_v_backup_job_model import HyperVBackupJobModel
    from ..models.linux_agent_management_backup_job_model import LinuxAgentManagementBackupJobModel
    from ..models.linux_agent_management_backup_server_policy_model import LinuxAgentManagementBackupServerPolicyModel
    from ..models.linux_agent_management_backup_workstation_policy_model import (
        LinuxAgentManagementBackupWorkstationPolicyModel,
    )
    from ..models.object_storage_backup_job_model import ObjectStorageBackupJobModel
    from ..models.pagination_result import PaginationResult
    from ..models.sure_backup_content_scan_job_model import SureBackupContentScanJobModel
    from ..models.v_sphere_replica_job_model import VSphereReplicaJobModel
    from ..models.windows_agent_management_backup_job_model import WindowsAgentManagementBackupJobModel
    from ..models.windows_agent_management_backup_server_policy_model import (
        WindowsAgentManagementBackupServerPolicyModel,
    )
    from ..models.windows_agent_management_backup_workstation_policy_model import (
        WindowsAgentManagementBackupWorkstationPolicyModel,
    )


T = TypeVar("T", bound="JobsResult")


@_attrs_define
class JobsResult:
    """Job details.

    Attributes:
        data (list[Union['BackupCopyJobModel', 'BackupJobModel', 'CloudDirectorBackupJobModel',
            'EntraIDAuditLogBackupJobModel', 'EntraIDTenantBackupCopyJobModel', 'EntraIDTenantBackupJobModel',
            'FileBackupCopyJobModel', 'FileBackupJobModel', 'HyperVBackupJobModel', 'LinuxAgentManagementBackupJobModel',
            'LinuxAgentManagementBackupServerPolicyModel', 'LinuxAgentManagementBackupWorkstationPolicyModel',
            'ObjectStorageBackupJobModel', 'SureBackupContentScanJobModel', 'VSphereReplicaJobModel',
            'WindowsAgentManagementBackupJobModel', 'WindowsAgentManagementBackupServerPolicyModel',
            'WindowsAgentManagementBackupWorkstationPolicyModel']]): Array of jobs.
        pagination (PaginationResult): Pagination settings.
    """

    data: list[
        Union[
            "BackupCopyJobModel",
            "BackupJobModel",
            "CloudDirectorBackupJobModel",
            "EntraIDAuditLogBackupJobModel",
            "EntraIDTenantBackupCopyJobModel",
            "EntraIDTenantBackupJobModel",
            "FileBackupCopyJobModel",
            "FileBackupJobModel",
            "HyperVBackupJobModel",
            "LinuxAgentManagementBackupJobModel",
            "LinuxAgentManagementBackupServerPolicyModel",
            "LinuxAgentManagementBackupWorkstationPolicyModel",
            "ObjectStorageBackupJobModel",
            "SureBackupContentScanJobModel",
            "VSphereReplicaJobModel",
            "WindowsAgentManagementBackupJobModel",
            "WindowsAgentManagementBackupServerPolicyModel",
            "WindowsAgentManagementBackupWorkstationPolicyModel",
        ]
    ]
    pagination: "PaginationResult"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.backup_copy_job_model import BackupCopyJobModel
        from ..models.backup_job_model import BackupJobModel
        from ..models.cloud_director_backup_job_model import CloudDirectorBackupJobModel
        from ..models.entra_id_audit_log_backup_job_model import EntraIDAuditLogBackupJobModel
        from ..models.entra_id_tenant_backup_copy_job_model import EntraIDTenantBackupCopyJobModel
        from ..models.entra_id_tenant_backup_job_model import EntraIDTenantBackupJobModel
        from ..models.file_backup_copy_job_model import FileBackupCopyJobModel
        from ..models.file_backup_job_model import FileBackupJobModel
        from ..models.hyper_v_backup_job_model import HyperVBackupJobModel
        from ..models.linux_agent_management_backup_job_model import LinuxAgentManagementBackupJobModel
        from ..models.linux_agent_management_backup_server_policy_model import (
            LinuxAgentManagementBackupServerPolicyModel,
        )
        from ..models.linux_agent_management_backup_workstation_policy_model import (
            LinuxAgentManagementBackupWorkstationPolicyModel,
        )
        from ..models.object_storage_backup_job_model import ObjectStorageBackupJobModel
        from ..models.v_sphere_replica_job_model import VSphereReplicaJobModel
        from ..models.windows_agent_management_backup_job_model import WindowsAgentManagementBackupJobModel
        from ..models.windows_agent_management_backup_server_policy_model import (
            WindowsAgentManagementBackupServerPolicyModel,
        )
        from ..models.windows_agent_management_backup_workstation_policy_model import (
            WindowsAgentManagementBackupWorkstationPolicyModel,
        )

        data = []
        for data_item_data in self.data:
            data_item: dict[str, Any]
            if isinstance(data_item_data, BackupJobModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, BackupCopyJobModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, HyperVBackupJobModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, CloudDirectorBackupJobModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, VSphereReplicaJobModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, EntraIDTenantBackupJobModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, EntraIDAuditLogBackupJobModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, FileBackupCopyJobModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, WindowsAgentManagementBackupJobModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, LinuxAgentManagementBackupJobModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, WindowsAgentManagementBackupWorkstationPolicyModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, LinuxAgentManagementBackupWorkstationPolicyModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, WindowsAgentManagementBackupServerPolicyModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, LinuxAgentManagementBackupServerPolicyModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, FileBackupJobModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, ObjectStorageBackupJobModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, EntraIDTenantBackupCopyJobModel):
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
        from ..models.backup_copy_job_model import BackupCopyJobModel
        from ..models.backup_job_model import BackupJobModel
        from ..models.cloud_director_backup_job_model import CloudDirectorBackupJobModel
        from ..models.entra_id_audit_log_backup_job_model import EntraIDAuditLogBackupJobModel
        from ..models.entra_id_tenant_backup_copy_job_model import EntraIDTenantBackupCopyJobModel
        from ..models.entra_id_tenant_backup_job_model import EntraIDTenantBackupJobModel
        from ..models.file_backup_copy_job_model import FileBackupCopyJobModel
        from ..models.file_backup_job_model import FileBackupJobModel
        from ..models.hyper_v_backup_job_model import HyperVBackupJobModel
        from ..models.linux_agent_management_backup_job_model import LinuxAgentManagementBackupJobModel
        from ..models.linux_agent_management_backup_server_policy_model import (
            LinuxAgentManagementBackupServerPolicyModel,
        )
        from ..models.linux_agent_management_backup_workstation_policy_model import (
            LinuxAgentManagementBackupWorkstationPolicyModel,
        )
        from ..models.object_storage_backup_job_model import ObjectStorageBackupJobModel
        from ..models.pagination_result import PaginationResult
        from ..models.sure_backup_content_scan_job_model import SureBackupContentScanJobModel
        from ..models.v_sphere_replica_job_model import VSphereReplicaJobModel
        from ..models.windows_agent_management_backup_job_model import WindowsAgentManagementBackupJobModel
        from ..models.windows_agent_management_backup_server_policy_model import (
            WindowsAgentManagementBackupServerPolicyModel,
        )
        from ..models.windows_agent_management_backup_workstation_policy_model import (
            WindowsAgentManagementBackupWorkstationPolicyModel,
        )

        d = dict(src_dict)
        data = []
        _data = d.pop("data")
        for data_item_data in _data:

            def _parse_data_item(
                data: object,
            ) -> Union[
                "BackupCopyJobModel",
                "BackupJobModel",
                "CloudDirectorBackupJobModel",
                "EntraIDAuditLogBackupJobModel",
                "EntraIDTenantBackupCopyJobModel",
                "EntraIDTenantBackupJobModel",
                "FileBackupCopyJobModel",
                "FileBackupJobModel",
                "HyperVBackupJobModel",
                "LinuxAgentManagementBackupJobModel",
                "LinuxAgentManagementBackupServerPolicyModel",
                "LinuxAgentManagementBackupWorkstationPolicyModel",
                "ObjectStorageBackupJobModel",
                "SureBackupContentScanJobModel",
                "VSphereReplicaJobModel",
                "WindowsAgentManagementBackupJobModel",
                "WindowsAgentManagementBackupServerPolicyModel",
                "WindowsAgentManagementBackupWorkstationPolicyModel",
            ]:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_job_model_type_0 = BackupJobModel.from_dict(data)

                    return componentsschemas_job_model_type_0
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_job_model_type_1 = BackupCopyJobModel.from_dict(data)

                    return componentsschemas_job_model_type_1
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_job_model_type_2 = HyperVBackupJobModel.from_dict(data)

                    return componentsschemas_job_model_type_2
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_job_model_type_3 = CloudDirectorBackupJobModel.from_dict(data)

                    return componentsschemas_job_model_type_3
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_job_model_type_4 = VSphereReplicaJobModel.from_dict(data)

                    return componentsschemas_job_model_type_4
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_job_model_type_5 = EntraIDTenantBackupJobModel.from_dict(data)

                    return componentsschemas_job_model_type_5
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_job_model_type_6 = EntraIDAuditLogBackupJobModel.from_dict(data)

                    return componentsschemas_job_model_type_6
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_job_model_type_7 = FileBackupCopyJobModel.from_dict(data)

                    return componentsschemas_job_model_type_7
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_job_model_type_8 = WindowsAgentManagementBackupJobModel.from_dict(data)

                    return componentsschemas_job_model_type_8
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_job_model_type_9 = LinuxAgentManagementBackupJobModel.from_dict(data)

                    return componentsschemas_job_model_type_9
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_job_model_type_10 = WindowsAgentManagementBackupWorkstationPolicyModel.from_dict(
                        data
                    )

                    return componentsschemas_job_model_type_10
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_job_model_type_11 = LinuxAgentManagementBackupWorkstationPolicyModel.from_dict(
                        data
                    )

                    return componentsschemas_job_model_type_11
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_job_model_type_12 = WindowsAgentManagementBackupServerPolicyModel.from_dict(data)

                    return componentsschemas_job_model_type_12
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_job_model_type_13 = LinuxAgentManagementBackupServerPolicyModel.from_dict(data)

                    return componentsschemas_job_model_type_13
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_job_model_type_14 = FileBackupJobModel.from_dict(data)

                    return componentsschemas_job_model_type_14
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_job_model_type_15 = ObjectStorageBackupJobModel.from_dict(data)

                    return componentsschemas_job_model_type_15
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_job_model_type_16 = EntraIDTenantBackupCopyJobModel.from_dict(data)

                    return componentsschemas_job_model_type_16
                except:  # noqa: E722
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_job_model_type_17 = SureBackupContentScanJobModel.from_dict(data)

                return componentsschemas_job_model_type_17

            data_item = _parse_data_item(data_item_data)

            data.append(data_item)

        pagination = PaginationResult.from_dict(d.pop("pagination"))

        jobs_result = cls(
            data=data,
            pagination=pagination,
        )

        jobs_result.additional_properties = d
        return jobs_result

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
