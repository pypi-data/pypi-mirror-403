from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.backup_copy_job_model import BackupCopyJobModel
from ...models.backup_copy_job_spec import BackupCopyJobSpec
from ...models.backup_job_model import BackupJobModel
from ...models.backup_job_spec import BackupJobSpec
from ...models.cloud_director_backup_job_model import CloudDirectorBackupJobModel
from ...models.cloud_director_backup_job_spec import CloudDirectorBackupJobSpec
from ...models.entra_id_audit_log_backup_job_model import EntraIDAuditLogBackupJobModel
from ...models.entra_id_audit_log_backup_job_spec import EntraIDAuditLogBackupJobSpec
from ...models.entra_id_tenant_backup_copy_job_model import EntraIDTenantBackupCopyJobModel
from ...models.entra_id_tenant_backup_copy_job_spec import EntraIDTenantBackupCopyJobSpec
from ...models.entra_id_tenant_backup_job_model import EntraIDTenantBackupJobModel
from ...models.entra_id_tenant_backup_job_spec import EntraIDTenantBackupJobSpec
from ...models.error import Error
from ...models.file_backup_copy_job_model import FileBackupCopyJobModel
from ...models.file_backup_copy_job_spec import FileBackupCopyJobSpec
from ...models.file_backup_job_model import FileBackupJobModel
from ...models.file_backup_job_spec import FileBackupJobSpec
from ...models.hyper_v_backup_job_model import HyperVBackupJobModel
from ...models.hyper_v_backup_job_spec import HyperVBackupJobSpec
from ...models.linux_agent_management_backup_job_model import LinuxAgentManagementBackupJobModel
from ...models.linux_agent_management_backup_job_spec import LinuxAgentManagementBackupJobSpec
from ...models.linux_agent_management_backup_server_policy_model import LinuxAgentManagementBackupServerPolicyModel
from ...models.linux_agent_management_backup_server_policy_spec import LinuxAgentManagementBackupServerPolicySpec
from ...models.linux_agent_management_backup_workstation_policy_model import (
    LinuxAgentManagementBackupWorkstationPolicyModel,
)
from ...models.linux_agent_management_backup_workstation_policy_spec import (
    LinuxAgentManagementBackupWorkstationPolicySpec,
)
from ...models.object_storage_backup_job_model import ObjectStorageBackupJobModel
from ...models.object_storage_backup_job_spec import ObjectStorageBackupJobSpec
from ...models.sure_backup_content_scan_job_model import SureBackupContentScanJobModel
from ...models.sure_backup_content_scan_job_spec import SureBackupContentScanJobSpec
from ...models.v_sphere_replica_job_model import VSphereReplicaJobModel
from ...models.v_sphere_replica_job_spec import VSphereReplicaJobSpec
from ...models.windows_agent_management_backup_job_model import WindowsAgentManagementBackupJobModel
from ...models.windows_agent_management_backup_job_spec import WindowsAgentManagementBackupJobSpec
from ...models.windows_agent_management_backup_server_policy_model import WindowsAgentManagementBackupServerPolicyModel
from ...models.windows_agent_management_backup_server_policy_spec import WindowsAgentManagementBackupServerPolicySpec
from ...models.windows_agent_management_backup_workstation_policy_model import (
    WindowsAgentManagementBackupWorkstationPolicyModel,
)
from ...models.windows_agent_management_backup_workstation_policy_spec import (
    WindowsAgentManagementBackupWorkstationPolicySpec,
)
from ...types import Response


def _get_kwargs(
    *,
    body: Union[
        "BackupCopyJobSpec",
        "BackupJobSpec",
        "CloudDirectorBackupJobSpec",
        "EntraIDAuditLogBackupJobSpec",
        "EntraIDTenantBackupCopyJobSpec",
        "EntraIDTenantBackupJobSpec",
        "FileBackupCopyJobSpec",
        "FileBackupJobSpec",
        "HyperVBackupJobSpec",
        "LinuxAgentManagementBackupJobSpec",
        "LinuxAgentManagementBackupServerPolicySpec",
        "LinuxAgentManagementBackupWorkstationPolicySpec",
        "ObjectStorageBackupJobSpec",
        "SureBackupContentScanJobSpec",
        "VSphereReplicaJobSpec",
        "WindowsAgentManagementBackupJobSpec",
        "WindowsAgentManagementBackupServerPolicySpec",
        "WindowsAgentManagementBackupWorkstationPolicySpec",
    ],
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/jobs",
    }

    _kwargs["json"]: dict[str, Any]
    if isinstance(body, BackupJobSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, BackupCopyJobSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, HyperVBackupJobSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, CloudDirectorBackupJobSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, VSphereReplicaJobSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, EntraIDTenantBackupJobSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, EntraIDAuditLogBackupJobSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, FileBackupCopyJobSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, WindowsAgentManagementBackupJobSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, LinuxAgentManagementBackupJobSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, WindowsAgentManagementBackupWorkstationPolicySpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, WindowsAgentManagementBackupServerPolicySpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, LinuxAgentManagementBackupWorkstationPolicySpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, LinuxAgentManagementBackupServerPolicySpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, FileBackupJobSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, ObjectStorageBackupJobSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, EntraIDTenantBackupCopyJobSpec):
        _kwargs["json"] = body.to_dict()
    else:
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        Error,
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
        ],
    ]
]:
    if response.status_code == 201:

        def _parse_response_201(
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
                componentsschemas_job_model_type_10 = WindowsAgentManagementBackupWorkstationPolicyModel.from_dict(data)

                return componentsschemas_job_model_type_10
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_job_model_type_11 = LinuxAgentManagementBackupWorkstationPolicyModel.from_dict(data)

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

        response_201 = _parse_response_201(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = Error.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = Error.from_dict(response.json())

        return response_403

    if response.status_code == 500:
        response_500 = Error.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        Error,
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
        ],
    ]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        "BackupCopyJobSpec",
        "BackupJobSpec",
        "CloudDirectorBackupJobSpec",
        "EntraIDAuditLogBackupJobSpec",
        "EntraIDTenantBackupCopyJobSpec",
        "EntraIDTenantBackupJobSpec",
        "FileBackupCopyJobSpec",
        "FileBackupJobSpec",
        "HyperVBackupJobSpec",
        "LinuxAgentManagementBackupJobSpec",
        "LinuxAgentManagementBackupServerPolicySpec",
        "LinuxAgentManagementBackupWorkstationPolicySpec",
        "ObjectStorageBackupJobSpec",
        "SureBackupContentScanJobSpec",
        "VSphereReplicaJobSpec",
        "WindowsAgentManagementBackupJobSpec",
        "WindowsAgentManagementBackupServerPolicySpec",
        "WindowsAgentManagementBackupWorkstationPolicySpec",
    ],
    x_api_version: str = "1.3-rev1",
) -> Response[
    Union[
        Error,
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
        ],
    ]
]:
    """Create Job

     The HTTP POST request to the `/api/v1/jobs` endpoint creates a new job that has the specified
    parameters.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (Union['BackupCopyJobSpec', 'BackupJobSpec', 'CloudDirectorBackupJobSpec',
            'EntraIDAuditLogBackupJobSpec', 'EntraIDTenantBackupCopyJobSpec',
            'EntraIDTenantBackupJobSpec', 'FileBackupCopyJobSpec', 'FileBackupJobSpec',
            'HyperVBackupJobSpec', 'LinuxAgentManagementBackupJobSpec',
            'LinuxAgentManagementBackupServerPolicySpec',
            'LinuxAgentManagementBackupWorkstationPolicySpec', 'ObjectStorageBackupJobSpec',
            'SureBackupContentScanJobSpec', 'VSphereReplicaJobSpec',
            'WindowsAgentManagementBackupJobSpec', 'WindowsAgentManagementBackupServerPolicySpec',
            'WindowsAgentManagementBackupWorkstationPolicySpec']): Job settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['BackupCopyJobModel', 'BackupJobModel', 'CloudDirectorBackupJobModel', 'EntraIDAuditLogBackupJobModel', 'EntraIDTenantBackupCopyJobModel', 'EntraIDTenantBackupJobModel', 'FileBackupCopyJobModel', 'FileBackupJobModel', 'HyperVBackupJobModel', 'LinuxAgentManagementBackupJobModel', 'LinuxAgentManagementBackupServerPolicyModel', 'LinuxAgentManagementBackupWorkstationPolicyModel', 'ObjectStorageBackupJobModel', 'SureBackupContentScanJobModel', 'VSphereReplicaJobModel', 'WindowsAgentManagementBackupJobModel', 'WindowsAgentManagementBackupServerPolicyModel', 'WindowsAgentManagementBackupWorkstationPolicyModel']]]
    """

    kwargs = _get_kwargs(
        body=body,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        "BackupCopyJobSpec",
        "BackupJobSpec",
        "CloudDirectorBackupJobSpec",
        "EntraIDAuditLogBackupJobSpec",
        "EntraIDTenantBackupCopyJobSpec",
        "EntraIDTenantBackupJobSpec",
        "FileBackupCopyJobSpec",
        "FileBackupJobSpec",
        "HyperVBackupJobSpec",
        "LinuxAgentManagementBackupJobSpec",
        "LinuxAgentManagementBackupServerPolicySpec",
        "LinuxAgentManagementBackupWorkstationPolicySpec",
        "ObjectStorageBackupJobSpec",
        "SureBackupContentScanJobSpec",
        "VSphereReplicaJobSpec",
        "WindowsAgentManagementBackupJobSpec",
        "WindowsAgentManagementBackupServerPolicySpec",
        "WindowsAgentManagementBackupWorkstationPolicySpec",
    ],
    x_api_version: str = "1.3-rev1",
) -> Optional[
    Union[
        Error,
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
        ],
    ]
]:
    """Create Job

     The HTTP POST request to the `/api/v1/jobs` endpoint creates a new job that has the specified
    parameters.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (Union['BackupCopyJobSpec', 'BackupJobSpec', 'CloudDirectorBackupJobSpec',
            'EntraIDAuditLogBackupJobSpec', 'EntraIDTenantBackupCopyJobSpec',
            'EntraIDTenantBackupJobSpec', 'FileBackupCopyJobSpec', 'FileBackupJobSpec',
            'HyperVBackupJobSpec', 'LinuxAgentManagementBackupJobSpec',
            'LinuxAgentManagementBackupServerPolicySpec',
            'LinuxAgentManagementBackupWorkstationPolicySpec', 'ObjectStorageBackupJobSpec',
            'SureBackupContentScanJobSpec', 'VSphereReplicaJobSpec',
            'WindowsAgentManagementBackupJobSpec', 'WindowsAgentManagementBackupServerPolicySpec',
            'WindowsAgentManagementBackupWorkstationPolicySpec']): Job settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['BackupCopyJobModel', 'BackupJobModel', 'CloudDirectorBackupJobModel', 'EntraIDAuditLogBackupJobModel', 'EntraIDTenantBackupCopyJobModel', 'EntraIDTenantBackupJobModel', 'FileBackupCopyJobModel', 'FileBackupJobModel', 'HyperVBackupJobModel', 'LinuxAgentManagementBackupJobModel', 'LinuxAgentManagementBackupServerPolicyModel', 'LinuxAgentManagementBackupWorkstationPolicyModel', 'ObjectStorageBackupJobModel', 'SureBackupContentScanJobModel', 'VSphereReplicaJobModel', 'WindowsAgentManagementBackupJobModel', 'WindowsAgentManagementBackupServerPolicyModel', 'WindowsAgentManagementBackupWorkstationPolicyModel']]
    """

    return sync_detailed(
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        "BackupCopyJobSpec",
        "BackupJobSpec",
        "CloudDirectorBackupJobSpec",
        "EntraIDAuditLogBackupJobSpec",
        "EntraIDTenantBackupCopyJobSpec",
        "EntraIDTenantBackupJobSpec",
        "FileBackupCopyJobSpec",
        "FileBackupJobSpec",
        "HyperVBackupJobSpec",
        "LinuxAgentManagementBackupJobSpec",
        "LinuxAgentManagementBackupServerPolicySpec",
        "LinuxAgentManagementBackupWorkstationPolicySpec",
        "ObjectStorageBackupJobSpec",
        "SureBackupContentScanJobSpec",
        "VSphereReplicaJobSpec",
        "WindowsAgentManagementBackupJobSpec",
        "WindowsAgentManagementBackupServerPolicySpec",
        "WindowsAgentManagementBackupWorkstationPolicySpec",
    ],
    x_api_version: str = "1.3-rev1",
) -> Response[
    Union[
        Error,
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
        ],
    ]
]:
    """Create Job

     The HTTP POST request to the `/api/v1/jobs` endpoint creates a new job that has the specified
    parameters.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (Union['BackupCopyJobSpec', 'BackupJobSpec', 'CloudDirectorBackupJobSpec',
            'EntraIDAuditLogBackupJobSpec', 'EntraIDTenantBackupCopyJobSpec',
            'EntraIDTenantBackupJobSpec', 'FileBackupCopyJobSpec', 'FileBackupJobSpec',
            'HyperVBackupJobSpec', 'LinuxAgentManagementBackupJobSpec',
            'LinuxAgentManagementBackupServerPolicySpec',
            'LinuxAgentManagementBackupWorkstationPolicySpec', 'ObjectStorageBackupJobSpec',
            'SureBackupContentScanJobSpec', 'VSphereReplicaJobSpec',
            'WindowsAgentManagementBackupJobSpec', 'WindowsAgentManagementBackupServerPolicySpec',
            'WindowsAgentManagementBackupWorkstationPolicySpec']): Job settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['BackupCopyJobModel', 'BackupJobModel', 'CloudDirectorBackupJobModel', 'EntraIDAuditLogBackupJobModel', 'EntraIDTenantBackupCopyJobModel', 'EntraIDTenantBackupJobModel', 'FileBackupCopyJobModel', 'FileBackupJobModel', 'HyperVBackupJobModel', 'LinuxAgentManagementBackupJobModel', 'LinuxAgentManagementBackupServerPolicyModel', 'LinuxAgentManagementBackupWorkstationPolicyModel', 'ObjectStorageBackupJobModel', 'SureBackupContentScanJobModel', 'VSphereReplicaJobModel', 'WindowsAgentManagementBackupJobModel', 'WindowsAgentManagementBackupServerPolicyModel', 'WindowsAgentManagementBackupWorkstationPolicyModel']]]
    """

    kwargs = _get_kwargs(
        body=body,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        "BackupCopyJobSpec",
        "BackupJobSpec",
        "CloudDirectorBackupJobSpec",
        "EntraIDAuditLogBackupJobSpec",
        "EntraIDTenantBackupCopyJobSpec",
        "EntraIDTenantBackupJobSpec",
        "FileBackupCopyJobSpec",
        "FileBackupJobSpec",
        "HyperVBackupJobSpec",
        "LinuxAgentManagementBackupJobSpec",
        "LinuxAgentManagementBackupServerPolicySpec",
        "LinuxAgentManagementBackupWorkstationPolicySpec",
        "ObjectStorageBackupJobSpec",
        "SureBackupContentScanJobSpec",
        "VSphereReplicaJobSpec",
        "WindowsAgentManagementBackupJobSpec",
        "WindowsAgentManagementBackupServerPolicySpec",
        "WindowsAgentManagementBackupWorkstationPolicySpec",
    ],
    x_api_version: str = "1.3-rev1",
) -> Optional[
    Union[
        Error,
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
        ],
    ]
]:
    """Create Job

     The HTTP POST request to the `/api/v1/jobs` endpoint creates a new job that has the specified
    parameters.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (Union['BackupCopyJobSpec', 'BackupJobSpec', 'CloudDirectorBackupJobSpec',
            'EntraIDAuditLogBackupJobSpec', 'EntraIDTenantBackupCopyJobSpec',
            'EntraIDTenantBackupJobSpec', 'FileBackupCopyJobSpec', 'FileBackupJobSpec',
            'HyperVBackupJobSpec', 'LinuxAgentManagementBackupJobSpec',
            'LinuxAgentManagementBackupServerPolicySpec',
            'LinuxAgentManagementBackupWorkstationPolicySpec', 'ObjectStorageBackupJobSpec',
            'SureBackupContentScanJobSpec', 'VSphereReplicaJobSpec',
            'WindowsAgentManagementBackupJobSpec', 'WindowsAgentManagementBackupServerPolicySpec',
            'WindowsAgentManagementBackupWorkstationPolicySpec']): Job settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['BackupCopyJobModel', 'BackupJobModel', 'CloudDirectorBackupJobModel', 'EntraIDAuditLogBackupJobModel', 'EntraIDTenantBackupCopyJobModel', 'EntraIDTenantBackupJobModel', 'FileBackupCopyJobModel', 'FileBackupJobModel', 'HyperVBackupJobModel', 'LinuxAgentManagementBackupJobModel', 'LinuxAgentManagementBackupServerPolicyModel', 'LinuxAgentManagementBackupWorkstationPolicyModel', 'ObjectStorageBackupJobModel', 'SureBackupContentScanJobModel', 'VSphereReplicaJobModel', 'WindowsAgentManagementBackupJobModel', 'WindowsAgentManagementBackupServerPolicyModel', 'WindowsAgentManagementBackupWorkstationPolicyModel']]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed
