from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.amazon_s3_glacier_storage_model import AmazonS3GlacierStorageModel
from ...models.amazon_s3_storage_model import AmazonS3StorageModel
from ...models.amazon_snowball_edge_storage_model import AmazonSnowballEdgeStorageModel
from ...models.azure_archive_storage_model import AzureArchiveStorageModel
from ...models.azure_blob_storage_model import AzureBlobStorageModel
from ...models.azure_data_box_storage_model import AzureDataBoxStorageModel
from ...models.error import Error
from ...models.google_cloud_storage_model import GoogleCloudStorageModel
from ...models.ibm_cloud_storage_model import IBMCloudStorageModel
from ...models.linux_hardened_storage_model import LinuxHardenedStorageModel
from ...models.linux_local_storage_model import LinuxLocalStorageModel
from ...models.nfs_storage_model import NfsStorageModel
from ...models.s3_compatible_storage_model import S3CompatibleStorageModel
from ...models.session_model import SessionModel
from ...models.smb_storage_model import SmbStorageModel
from ...models.veeam_data_cloud_vault_storage_model import VeeamDataCloudVaultStorageModel
from ...models.wasabi_cloud_storage_model import WasabiCloudStorageModel
from ...models.windows_local_storage_model import WindowsLocalStorageModel
from ...types import Response


def _get_kwargs(
    id: UUID,
    *,
    body: Union[
        "AmazonS3GlacierStorageModel",
        "AmazonS3StorageModel",
        "AmazonSnowballEdgeStorageModel",
        "AzureArchiveStorageModel",
        "AzureBlobStorageModel",
        "AzureDataBoxStorageModel",
        "GoogleCloudStorageModel",
        "IBMCloudStorageModel",
        "LinuxHardenedStorageModel",
        "LinuxLocalStorageModel",
        "NfsStorageModel",
        "S3CompatibleStorageModel",
        "SmbStorageModel",
        "VeeamDataCloudVaultStorageModel",
        "WasabiCloudStorageModel",
        "WindowsLocalStorageModel",
    ],
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/api/v1/backupInfrastructure/repositories/{id}",
    }

    _kwargs["json"]: dict[str, Any]
    if isinstance(body, WindowsLocalStorageModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, LinuxLocalStorageModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, NfsStorageModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, SmbStorageModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AzureBlobStorageModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AzureDataBoxStorageModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AmazonS3StorageModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AmazonSnowballEdgeStorageModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, S3CompatibleStorageModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, GoogleCloudStorageModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, IBMCloudStorageModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AmazonS3GlacierStorageModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AzureArchiveStorageModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, WasabiCloudStorageModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, LinuxHardenedStorageModel):
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
        "AmazonS3GlacierStorageModel",
        "AmazonS3StorageModel",
        "AmazonSnowballEdgeStorageModel",
        "AzureArchiveStorageModel",
        "AzureBlobStorageModel",
        "AzureDataBoxStorageModel",
        "GoogleCloudStorageModel",
        "IBMCloudStorageModel",
        "LinuxHardenedStorageModel",
        "LinuxLocalStorageModel",
        "NfsStorageModel",
        "S3CompatibleStorageModel",
        "SmbStorageModel",
        "VeeamDataCloudVaultStorageModel",
        "WasabiCloudStorageModel",
        "WindowsLocalStorageModel",
    ],
    x_api_version: str = "1.3-rev1",
) -> Response[Union[Error, SessionModel]]:
    """Edit Repository

     The HTTP PUT request to the `/api/v1/backupInfrastructure/repositories/{id}` endpoint edits a backup
    repository that has the specified `id`.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (Union['AmazonS3GlacierStorageModel', 'AmazonS3StorageModel',
            'AmazonSnowballEdgeStorageModel', 'AzureArchiveStorageModel', 'AzureBlobStorageModel',
            'AzureDataBoxStorageModel', 'GoogleCloudStorageModel', 'IBMCloudStorageModel',
            'LinuxHardenedStorageModel', 'LinuxLocalStorageModel', 'NfsStorageModel',
            'S3CompatibleStorageModel', 'SmbStorageModel', 'VeeamDataCloudVaultStorageModel',
            'WasabiCloudStorageModel', 'WindowsLocalStorageModel']): Backup repository.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, SessionModel]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
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
        "AmazonS3GlacierStorageModel",
        "AmazonS3StorageModel",
        "AmazonSnowballEdgeStorageModel",
        "AzureArchiveStorageModel",
        "AzureBlobStorageModel",
        "AzureDataBoxStorageModel",
        "GoogleCloudStorageModel",
        "IBMCloudStorageModel",
        "LinuxHardenedStorageModel",
        "LinuxLocalStorageModel",
        "NfsStorageModel",
        "S3CompatibleStorageModel",
        "SmbStorageModel",
        "VeeamDataCloudVaultStorageModel",
        "WasabiCloudStorageModel",
        "WindowsLocalStorageModel",
    ],
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[Error, SessionModel]]:
    """Edit Repository

     The HTTP PUT request to the `/api/v1/backupInfrastructure/repositories/{id}` endpoint edits a backup
    repository that has the specified `id`.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (Union['AmazonS3GlacierStorageModel', 'AmazonS3StorageModel',
            'AmazonSnowballEdgeStorageModel', 'AzureArchiveStorageModel', 'AzureBlobStorageModel',
            'AzureDataBoxStorageModel', 'GoogleCloudStorageModel', 'IBMCloudStorageModel',
            'LinuxHardenedStorageModel', 'LinuxLocalStorageModel', 'NfsStorageModel',
            'S3CompatibleStorageModel', 'SmbStorageModel', 'VeeamDataCloudVaultStorageModel',
            'WasabiCloudStorageModel', 'WindowsLocalStorageModel']): Backup repository.

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
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        "AmazonS3GlacierStorageModel",
        "AmazonS3StorageModel",
        "AmazonSnowballEdgeStorageModel",
        "AzureArchiveStorageModel",
        "AzureBlobStorageModel",
        "AzureDataBoxStorageModel",
        "GoogleCloudStorageModel",
        "IBMCloudStorageModel",
        "LinuxHardenedStorageModel",
        "LinuxLocalStorageModel",
        "NfsStorageModel",
        "S3CompatibleStorageModel",
        "SmbStorageModel",
        "VeeamDataCloudVaultStorageModel",
        "WasabiCloudStorageModel",
        "WindowsLocalStorageModel",
    ],
    x_api_version: str = "1.3-rev1",
) -> Response[Union[Error, SessionModel]]:
    """Edit Repository

     The HTTP PUT request to the `/api/v1/backupInfrastructure/repositories/{id}` endpoint edits a backup
    repository that has the specified `id`.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (Union['AmazonS3GlacierStorageModel', 'AmazonS3StorageModel',
            'AmazonSnowballEdgeStorageModel', 'AzureArchiveStorageModel', 'AzureBlobStorageModel',
            'AzureDataBoxStorageModel', 'GoogleCloudStorageModel', 'IBMCloudStorageModel',
            'LinuxHardenedStorageModel', 'LinuxLocalStorageModel', 'NfsStorageModel',
            'S3CompatibleStorageModel', 'SmbStorageModel', 'VeeamDataCloudVaultStorageModel',
            'WasabiCloudStorageModel', 'WindowsLocalStorageModel']): Backup repository.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, SessionModel]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        "AmazonS3GlacierStorageModel",
        "AmazonS3StorageModel",
        "AmazonSnowballEdgeStorageModel",
        "AzureArchiveStorageModel",
        "AzureBlobStorageModel",
        "AzureDataBoxStorageModel",
        "GoogleCloudStorageModel",
        "IBMCloudStorageModel",
        "LinuxHardenedStorageModel",
        "LinuxLocalStorageModel",
        "NfsStorageModel",
        "S3CompatibleStorageModel",
        "SmbStorageModel",
        "VeeamDataCloudVaultStorageModel",
        "WasabiCloudStorageModel",
        "WindowsLocalStorageModel",
    ],
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[Error, SessionModel]]:
    """Edit Repository

     The HTTP PUT request to the `/api/v1/backupInfrastructure/repositories/{id}` endpoint edits a backup
    repository that has the specified `id`.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (Union['AmazonS3GlacierStorageModel', 'AmazonS3StorageModel',
            'AmazonSnowballEdgeStorageModel', 'AzureArchiveStorageModel', 'AzureBlobStorageModel',
            'AzureDataBoxStorageModel', 'GoogleCloudStorageModel', 'IBMCloudStorageModel',
            'LinuxHardenedStorageModel', 'LinuxLocalStorageModel', 'NfsStorageModel',
            'S3CompatibleStorageModel', 'SmbStorageModel', 'VeeamDataCloudVaultStorageModel',
            'WasabiCloudStorageModel', 'WindowsLocalStorageModel']): Backup repository.

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
            x_api_version=x_api_version,
        )
    ).parsed
