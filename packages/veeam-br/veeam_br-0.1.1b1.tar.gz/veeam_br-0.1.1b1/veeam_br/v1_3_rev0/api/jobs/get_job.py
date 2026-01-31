from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.backup_copy_job_model import BackupCopyJobModel
from ...models.backup_job_model import BackupJobModel
from ...models.cloud_director_backup_job_model import CloudDirectorBackupJobModel
from ...models.entra_id_audit_log_backup_job_model import EntraIDAuditLogBackupJobModel
from ...models.entra_id_tenant_backup_copy_job_model import EntraIDTenantBackupCopyJobModel
from ...models.entra_id_tenant_backup_job_model import EntraIDTenantBackupJobModel
from ...models.error import Error
from ...models.file_backup_copy_job_model import FileBackupCopyJobModel
from ...models.hyper_v_backup_job_model import HyperVBackupJobModel
from ...models.linux_agent_management_backup_job_model import LinuxAgentManagementBackupJobModel
from ...models.v_sphere_replica_job_model import VSphereReplicaJobModel
from ...models.windows_agent_management_backup_job_model import WindowsAgentManagementBackupJobModel
from ...types import Response


def _get_kwargs(
    id: UUID,
    *,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/jobs/{id}",
    }

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
            "HyperVBackupJobModel",
            "LinuxAgentManagementBackupJobModel",
            "VSphereReplicaJobModel",
            "WindowsAgentManagementBackupJobModel",
        ],
    ]
]:
    if response.status_code == 200:

        def _parse_response_200(
            data: object,
        ) -> Union[
            "BackupCopyJobModel",
            "BackupJobModel",
            "CloudDirectorBackupJobModel",
            "EntraIDAuditLogBackupJobModel",
            "EntraIDTenantBackupCopyJobModel",
            "EntraIDTenantBackupJobModel",
            "FileBackupCopyJobModel",
            "HyperVBackupJobModel",
            "LinuxAgentManagementBackupJobModel",
            "VSphereReplicaJobModel",
            "WindowsAgentManagementBackupJobModel",
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
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_job_model_type_10 = EntraIDTenantBackupCopyJobModel.from_dict(data)

            return componentsschemas_job_model_type_10

        response_200 = _parse_response_200(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = Error.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = Error.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404

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
            "HyperVBackupJobModel",
            "LinuxAgentManagementBackupJobModel",
            "VSphereReplicaJobModel",
            "WindowsAgentManagementBackupJobModel",
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
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev0",
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
            "HyperVBackupJobModel",
            "LinuxAgentManagementBackupJobModel",
            "VSphereReplicaJobModel",
            "WindowsAgentManagementBackupJobModel",
        ],
    ]
]:
    """Get Job

     The HTTP GET request to the `/api/v1/jobs/{id}` path allows you to get a job that has the specified
    `id`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Backup Operator, Veeam Restore
    Operator, Veeam Backup Viewer, Veeam Tape Operator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['BackupCopyJobModel', 'BackupJobModel', 'CloudDirectorBackupJobModel', 'EntraIDAuditLogBackupJobModel', 'EntraIDTenantBackupCopyJobModel', 'EntraIDTenantBackupJobModel', 'FileBackupCopyJobModel', 'HyperVBackupJobModel', 'LinuxAgentManagementBackupJobModel', 'VSphereReplicaJobModel', 'WindowsAgentManagementBackupJobModel']]]
    """

    kwargs = _get_kwargs(
        id=id,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev0",
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
            "HyperVBackupJobModel",
            "LinuxAgentManagementBackupJobModel",
            "VSphereReplicaJobModel",
            "WindowsAgentManagementBackupJobModel",
        ],
    ]
]:
    """Get Job

     The HTTP GET request to the `/api/v1/jobs/{id}` path allows you to get a job that has the specified
    `id`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Backup Operator, Veeam Restore
    Operator, Veeam Backup Viewer, Veeam Tape Operator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['BackupCopyJobModel', 'BackupJobModel', 'CloudDirectorBackupJobModel', 'EntraIDAuditLogBackupJobModel', 'EntraIDTenantBackupCopyJobModel', 'EntraIDTenantBackupJobModel', 'FileBackupCopyJobModel', 'HyperVBackupJobModel', 'LinuxAgentManagementBackupJobModel', 'VSphereReplicaJobModel', 'WindowsAgentManagementBackupJobModel']]
    """

    return sync_detailed(
        id=id,
        client=client,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev0",
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
            "HyperVBackupJobModel",
            "LinuxAgentManagementBackupJobModel",
            "VSphereReplicaJobModel",
            "WindowsAgentManagementBackupJobModel",
        ],
    ]
]:
    """Get Job

     The HTTP GET request to the `/api/v1/jobs/{id}` path allows you to get a job that has the specified
    `id`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Backup Operator, Veeam Restore
    Operator, Veeam Backup Viewer, Veeam Tape Operator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['BackupCopyJobModel', 'BackupJobModel', 'CloudDirectorBackupJobModel', 'EntraIDAuditLogBackupJobModel', 'EntraIDTenantBackupCopyJobModel', 'EntraIDTenantBackupJobModel', 'FileBackupCopyJobModel', 'HyperVBackupJobModel', 'LinuxAgentManagementBackupJobModel', 'VSphereReplicaJobModel', 'WindowsAgentManagementBackupJobModel']]]
    """

    kwargs = _get_kwargs(
        id=id,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev0",
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
            "HyperVBackupJobModel",
            "LinuxAgentManagementBackupJobModel",
            "VSphereReplicaJobModel",
            "WindowsAgentManagementBackupJobModel",
        ],
    ]
]:
    """Get Job

     The HTTP GET request to the `/api/v1/jobs/{id}` path allows you to get a job that has the specified
    `id`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Backup Operator, Veeam Restore
    Operator, Veeam Backup Viewer, Veeam Tape Operator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['BackupCopyJobModel', 'BackupJobModel', 'CloudDirectorBackupJobModel', 'EntraIDAuditLogBackupJobModel', 'EntraIDTenantBackupCopyJobModel', 'EntraIDTenantBackupJobModel', 'FileBackupCopyJobModel', 'HyperVBackupJobModel', 'LinuxAgentManagementBackupJobModel', 'VSphereReplicaJobModel', 'WindowsAgentManagementBackupJobModel']]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed
