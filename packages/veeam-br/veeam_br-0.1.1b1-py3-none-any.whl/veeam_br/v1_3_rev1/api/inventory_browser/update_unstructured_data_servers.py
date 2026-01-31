from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.amazon_s3_server_model import AmazonS3ServerModel
from ...models.azure_blob_server_model import AzureBlobServerModel
from ...models.e_unstructured_data_meta_migration_type import EUnstructuredDataMetaMigrationType
from ...models.error import Error
from ...models.file_server_model import FileServerModel
from ...models.nas_filer_server_model import NASFilerServerModel
from ...models.nfs_share_server_model import NFSShareServerModel
from ...models.s3_compatible_server_model import S3CompatibleServerModel
from ...models.session_model import SessionModel
from ...models.smb_share_server_model import SMBShareServerModel
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: UUID,
    *,
    body: Union[
        "AmazonS3ServerModel",
        "AzureBlobServerModel",
        "FileServerModel",
        "NASFilerServerModel",
        "NFSShareServerModel",
        "S3CompatibleServerModel",
        "SMBShareServerModel",
    ],
    migration_type: Union[Unset, EUnstructuredDataMetaMigrationType] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    params: dict[str, Any] = {}

    json_migration_type: Union[Unset, str] = UNSET
    if not isinstance(migration_type, Unset):
        json_migration_type = migration_type.value

    params["migrationType"] = json_migration_type

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/api/v1/inventory/unstructuredDataServers/{id}",
        "params": params,
    }

    _kwargs["json"]: dict[str, Any]
    if isinstance(body, FileServerModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, SMBShareServerModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, NFSShareServerModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, NASFilerServerModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, S3CompatibleServerModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AmazonS3ServerModel):
        _kwargs["json"] = body.to_dict()
    else:
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, SessionModel]]:
    if response.status_code == 201:
        response_201 = SessionModel.from_dict(response.json())

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
) -> Response[Union[Error, SessionModel]]:
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
    body: Union[
        "AmazonS3ServerModel",
        "AzureBlobServerModel",
        "FileServerModel",
        "NASFilerServerModel",
        "NFSShareServerModel",
        "S3CompatibleServerModel",
        "SMBShareServerModel",
    ],
    migration_type: Union[Unset, EUnstructuredDataMetaMigrationType] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[Union[Error, SessionModel]]:
    """Edit Unstructured Data Server

     The HTTP PUT request to the `/api/v1/inventory/unstructuredDataServers/{id}` endpoint edits an
    unstructured data server that has the specified `id`.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        id (UUID):
        migration_type (Union[Unset, EUnstructuredDataMetaMigrationType]): Metadata migration
            type.
        x_api_version (str):  Default: '1.3-rev1'.
        body (Union['AmazonS3ServerModel', 'AzureBlobServerModel', 'FileServerModel',
            'NASFilerServerModel', 'NFSShareServerModel', 'S3CompatibleServerModel',
            'SMBShareServerModel']): Unstructured data server.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, SessionModel]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
        migration_type=migration_type,
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
    body: Union[
        "AmazonS3ServerModel",
        "AzureBlobServerModel",
        "FileServerModel",
        "NASFilerServerModel",
        "NFSShareServerModel",
        "S3CompatibleServerModel",
        "SMBShareServerModel",
    ],
    migration_type: Union[Unset, EUnstructuredDataMetaMigrationType] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[Error, SessionModel]]:
    """Edit Unstructured Data Server

     The HTTP PUT request to the `/api/v1/inventory/unstructuredDataServers/{id}` endpoint edits an
    unstructured data server that has the specified `id`.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        id (UUID):
        migration_type (Union[Unset, EUnstructuredDataMetaMigrationType]): Metadata migration
            type.
        x_api_version (str):  Default: '1.3-rev1'.
        body (Union['AmazonS3ServerModel', 'AzureBlobServerModel', 'FileServerModel',
            'NASFilerServerModel', 'NFSShareServerModel', 'S3CompatibleServerModel',
            'SMBShareServerModel']): Unstructured data server.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, SessionModel]
    """

    return sync_detailed(
        id=id,
        client=client,
        body=body,
        migration_type=migration_type,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        "AmazonS3ServerModel",
        "AzureBlobServerModel",
        "FileServerModel",
        "NASFilerServerModel",
        "NFSShareServerModel",
        "S3CompatibleServerModel",
        "SMBShareServerModel",
    ],
    migration_type: Union[Unset, EUnstructuredDataMetaMigrationType] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[Union[Error, SessionModel]]:
    """Edit Unstructured Data Server

     The HTTP PUT request to the `/api/v1/inventory/unstructuredDataServers/{id}` endpoint edits an
    unstructured data server that has the specified `id`.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        id (UUID):
        migration_type (Union[Unset, EUnstructuredDataMetaMigrationType]): Metadata migration
            type.
        x_api_version (str):  Default: '1.3-rev1'.
        body (Union['AmazonS3ServerModel', 'AzureBlobServerModel', 'FileServerModel',
            'NASFilerServerModel', 'NFSShareServerModel', 'S3CompatibleServerModel',
            'SMBShareServerModel']): Unstructured data server.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, SessionModel]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
        migration_type=migration_type,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        "AmazonS3ServerModel",
        "AzureBlobServerModel",
        "FileServerModel",
        "NASFilerServerModel",
        "NFSShareServerModel",
        "S3CompatibleServerModel",
        "SMBShareServerModel",
    ],
    migration_type: Union[Unset, EUnstructuredDataMetaMigrationType] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[Error, SessionModel]]:
    """Edit Unstructured Data Server

     The HTTP PUT request to the `/api/v1/inventory/unstructuredDataServers/{id}` endpoint edits an
    unstructured data server that has the specified `id`.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        id (UUID):
        migration_type (Union[Unset, EUnstructuredDataMetaMigrationType]): Metadata migration
            type.
        x_api_version (str):  Default: '1.3-rev1'.
        body (Union['AmazonS3ServerModel', 'AzureBlobServerModel', 'FileServerModel',
            'NASFilerServerModel', 'NFSShareServerModel', 'S3CompatibleServerModel',
            'SMBShareServerModel']): Unstructured data server.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, SessionModel]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
            migration_type=migration_type,
            x_api_version=x_api_version,
        )
    ).parsed
