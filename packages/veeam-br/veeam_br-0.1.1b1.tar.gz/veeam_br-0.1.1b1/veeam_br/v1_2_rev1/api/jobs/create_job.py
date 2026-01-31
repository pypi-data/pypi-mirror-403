from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.backup_job_model import BackupJobModel
from ...models.backup_job_spec import BackupJobSpec
from ...models.cloud_director_backup_job_model import CloudDirectorBackupJobModel
from ...models.cloud_director_backup_job_spec import CloudDirectorBackupJobSpec
from ...models.entra_id_audit_log_backup_job_model import EntraIDAuditLogBackupJobModel
from ...models.entra_id_audit_log_backup_job_spec import EntraIDAuditLogBackupJobSpec
from ...models.entra_id_tenant_backup_job_model import EntraIDTenantBackupJobModel
from ...models.entra_id_tenant_backup_job_spec import EntraIDTenantBackupJobSpec
from ...models.error import Error
from ...models.file_backup_copy_job_model import FileBackupCopyJobModel
from ...models.file_backup_copy_job_spec import FileBackupCopyJobSpec
from ...models.v_sphere_replica_job_model import VSphereReplicaJobModel
from ...models.v_sphere_replica_job_spec import VSphereReplicaJobSpec
from ...types import Response


def _get_kwargs(
    *,
    body: Union[
        "BackupJobSpec",
        "CloudDirectorBackupJobSpec",
        "EntraIDAuditLogBackupJobSpec",
        "EntraIDTenantBackupJobSpec",
        "FileBackupCopyJobSpec",
        "VSphereReplicaJobSpec",
    ],
    x_api_version: str = "1.2-rev1",
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
    elif isinstance(body, CloudDirectorBackupJobSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, VSphereReplicaJobSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, EntraIDTenantBackupJobSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, EntraIDAuditLogBackupJobSpec):
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
            "BackupJobModel",
            "CloudDirectorBackupJobModel",
            "EntraIDAuditLogBackupJobModel",
            "EntraIDTenantBackupJobModel",
            "FileBackupCopyJobModel",
            "VSphereReplicaJobModel",
        ],
    ]
]:
    if response.status_code == 201:

        def _parse_response_201(
            data: object,
        ) -> Union[
            "BackupJobModel",
            "CloudDirectorBackupJobModel",
            "EntraIDAuditLogBackupJobModel",
            "EntraIDTenantBackupJobModel",
            "FileBackupCopyJobModel",
            "VSphereReplicaJobModel",
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
                componentsschemas_job_model_type_1 = CloudDirectorBackupJobModel.from_dict(data)

                return componentsschemas_job_model_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_job_model_type_2 = VSphereReplicaJobModel.from_dict(data)

                return componentsschemas_job_model_type_2
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_job_model_type_3 = EntraIDTenantBackupJobModel.from_dict(data)

                return componentsschemas_job_model_type_3
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_job_model_type_4 = EntraIDAuditLogBackupJobModel.from_dict(data)

                return componentsschemas_job_model_type_4
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_job_model_type_5 = FileBackupCopyJobModel.from_dict(data)

            return componentsschemas_job_model_type_5

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
            "BackupJobModel",
            "CloudDirectorBackupJobModel",
            "EntraIDAuditLogBackupJobModel",
            "EntraIDTenantBackupJobModel",
            "FileBackupCopyJobModel",
            "VSphereReplicaJobModel",
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
        "BackupJobSpec",
        "CloudDirectorBackupJobSpec",
        "EntraIDAuditLogBackupJobSpec",
        "EntraIDTenantBackupJobSpec",
        "FileBackupCopyJobSpec",
        "VSphereReplicaJobSpec",
    ],
    x_api_version: str = "1.2-rev1",
) -> Response[
    Union[
        Error,
        Union[
            "BackupJobModel",
            "CloudDirectorBackupJobModel",
            "EntraIDAuditLogBackupJobModel",
            "EntraIDTenantBackupJobModel",
            "FileBackupCopyJobModel",
            "VSphereReplicaJobModel",
        ],
    ]
]:
    """Create Job

     The HTTP POST request to the `/api/v1/jobs` path allows you to create a new job that has the
    specified parameters.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.
        body (Union['BackupJobSpec', 'CloudDirectorBackupJobSpec', 'EntraIDAuditLogBackupJobSpec',
            'EntraIDTenantBackupJobSpec', 'FileBackupCopyJobSpec', 'VSphereReplicaJobSpec']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['BackupJobModel', 'CloudDirectorBackupJobModel', 'EntraIDAuditLogBackupJobModel', 'EntraIDTenantBackupJobModel', 'FileBackupCopyJobModel', 'VSphereReplicaJobModel']]]
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
        "BackupJobSpec",
        "CloudDirectorBackupJobSpec",
        "EntraIDAuditLogBackupJobSpec",
        "EntraIDTenantBackupJobSpec",
        "FileBackupCopyJobSpec",
        "VSphereReplicaJobSpec",
    ],
    x_api_version: str = "1.2-rev1",
) -> Optional[
    Union[
        Error,
        Union[
            "BackupJobModel",
            "CloudDirectorBackupJobModel",
            "EntraIDAuditLogBackupJobModel",
            "EntraIDTenantBackupJobModel",
            "FileBackupCopyJobModel",
            "VSphereReplicaJobModel",
        ],
    ]
]:
    """Create Job

     The HTTP POST request to the `/api/v1/jobs` path allows you to create a new job that has the
    specified parameters.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.
        body (Union['BackupJobSpec', 'CloudDirectorBackupJobSpec', 'EntraIDAuditLogBackupJobSpec',
            'EntraIDTenantBackupJobSpec', 'FileBackupCopyJobSpec', 'VSphereReplicaJobSpec']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['BackupJobModel', 'CloudDirectorBackupJobModel', 'EntraIDAuditLogBackupJobModel', 'EntraIDTenantBackupJobModel', 'FileBackupCopyJobModel', 'VSphereReplicaJobModel']]
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
        "BackupJobSpec",
        "CloudDirectorBackupJobSpec",
        "EntraIDAuditLogBackupJobSpec",
        "EntraIDTenantBackupJobSpec",
        "FileBackupCopyJobSpec",
        "VSphereReplicaJobSpec",
    ],
    x_api_version: str = "1.2-rev1",
) -> Response[
    Union[
        Error,
        Union[
            "BackupJobModel",
            "CloudDirectorBackupJobModel",
            "EntraIDAuditLogBackupJobModel",
            "EntraIDTenantBackupJobModel",
            "FileBackupCopyJobModel",
            "VSphereReplicaJobModel",
        ],
    ]
]:
    """Create Job

     The HTTP POST request to the `/api/v1/jobs` path allows you to create a new job that has the
    specified parameters.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.
        body (Union['BackupJobSpec', 'CloudDirectorBackupJobSpec', 'EntraIDAuditLogBackupJobSpec',
            'EntraIDTenantBackupJobSpec', 'FileBackupCopyJobSpec', 'VSphereReplicaJobSpec']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['BackupJobModel', 'CloudDirectorBackupJobModel', 'EntraIDAuditLogBackupJobModel', 'EntraIDTenantBackupJobModel', 'FileBackupCopyJobModel', 'VSphereReplicaJobModel']]]
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
        "BackupJobSpec",
        "CloudDirectorBackupJobSpec",
        "EntraIDAuditLogBackupJobSpec",
        "EntraIDTenantBackupJobSpec",
        "FileBackupCopyJobSpec",
        "VSphereReplicaJobSpec",
    ],
    x_api_version: str = "1.2-rev1",
) -> Optional[
    Union[
        Error,
        Union[
            "BackupJobModel",
            "CloudDirectorBackupJobModel",
            "EntraIDAuditLogBackupJobModel",
            "EntraIDTenantBackupJobModel",
            "FileBackupCopyJobModel",
            "VSphereReplicaJobModel",
        ],
    ]
]:
    """Create Job

     The HTTP POST request to the `/api/v1/jobs` path allows you to create a new job that has the
    specified parameters.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.
        body (Union['BackupJobSpec', 'CloudDirectorBackupJobSpec', 'EntraIDAuditLogBackupJobSpec',
            'EntraIDTenantBackupJobSpec', 'FileBackupCopyJobSpec', 'VSphereReplicaJobSpec']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['BackupJobModel', 'CloudDirectorBackupJobModel', 'EntraIDAuditLogBackupJobModel', 'EntraIDTenantBackupJobModel', 'FileBackupCopyJobModel', 'VSphereReplicaJobModel']]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed
