from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.amazon_s3_glacier_storage_spec import AmazonS3GlacierStorageSpec
from ...models.amazon_s3_storage_spec import AmazonS3StorageSpec
from ...models.amazon_snowball_edge_storage_spec import AmazonSnowballEdgeStorageSpec
from ...models.azure_archive_storage_spec import AzureArchiveStorageSpec
from ...models.azure_blob_storage_spec import AzureBlobStorageSpec
from ...models.azure_data_box_storage_spec import AzureDataBoxStorageSpec
from ...models.error import Error
from ...models.google_cloud_storage_spec import GoogleCloudStorageSpec
from ...models.ibm_cloud_storage_spec import IBMCloudStorageSpec
from ...models.linux_hardened_storage_spec import LinuxHardenedStorageSpec
from ...models.linux_local_storage_spec import LinuxLocalStorageSpec
from ...models.nfs_storage_spec import NfsStorageSpec
from ...models.s3_compatible_storage_spec import S3CompatibleStorageSpec
from ...models.session_model import SessionModel
from ...models.smb_storage_spec import SmbStorageSpec
from ...models.veeam_data_cloud_vault_storage_spec import VeeamDataCloudVaultStorageSpec
from ...models.wasabi_cloud_storage_spec import WasabiCloudStorageSpec
from ...models.windows_local_storage_spec import WindowsLocalStorageSpec
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: Union[
        "AmazonS3GlacierStorageSpec",
        "AmazonS3StorageSpec",
        "AmazonSnowballEdgeStorageSpec",
        "AzureArchiveStorageSpec",
        "AzureBlobStorageSpec",
        "AzureDataBoxStorageSpec",
        "GoogleCloudStorageSpec",
        "IBMCloudStorageSpec",
        "LinuxHardenedStorageSpec",
        "LinuxLocalStorageSpec",
        "NfsStorageSpec",
        "S3CompatibleStorageSpec",
        "SmbStorageSpec",
        "VeeamDataCloudVaultStorageSpec",
        "WasabiCloudStorageSpec",
        "WindowsLocalStorageSpec",
    ],
    overwrite_owner: Union[Unset, bool] = UNSET,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    params: dict[str, Any] = {}

    params["overwriteOwner"] = overwrite_owner

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/backupInfrastructure/repositories",
        "params": params,
    }

    _kwargs["json"]: dict[str, Any]
    if isinstance(body, WindowsLocalStorageSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, LinuxLocalStorageSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, NfsStorageSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, SmbStorageSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AzureBlobStorageSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AzureDataBoxStorageSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AmazonS3StorageSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AmazonSnowballEdgeStorageSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, S3CompatibleStorageSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, GoogleCloudStorageSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, IBMCloudStorageSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AmazonS3GlacierStorageSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AzureArchiveStorageSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, WasabiCloudStorageSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, LinuxHardenedStorageSpec):
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
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        "AmazonS3GlacierStorageSpec",
        "AmazonS3StorageSpec",
        "AmazonSnowballEdgeStorageSpec",
        "AzureArchiveStorageSpec",
        "AzureBlobStorageSpec",
        "AzureDataBoxStorageSpec",
        "GoogleCloudStorageSpec",
        "IBMCloudStorageSpec",
        "LinuxHardenedStorageSpec",
        "LinuxLocalStorageSpec",
        "NfsStorageSpec",
        "S3CompatibleStorageSpec",
        "SmbStorageSpec",
        "VeeamDataCloudVaultStorageSpec",
        "WasabiCloudStorageSpec",
        "WindowsLocalStorageSpec",
    ],
    overwrite_owner: Union[Unset, bool] = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[Union[Error, SessionModel]]:
    """Add Repository

     The HTTP POST request to the `/api/v1/backupInfrastructure/repositories` path allows you to add a
    repository to the backup infrastructure.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        overwrite_owner (Union[Unset, bool]):
        x_api_version (str):  Default: '1.3-rev0'.
        body (Union['AmazonS3GlacierStorageSpec', 'AmazonS3StorageSpec',
            'AmazonSnowballEdgeStorageSpec', 'AzureArchiveStorageSpec', 'AzureBlobStorageSpec',
            'AzureDataBoxStorageSpec', 'GoogleCloudStorageSpec', 'IBMCloudStorageSpec',
            'LinuxHardenedStorageSpec', 'LinuxLocalStorageSpec', 'NfsStorageSpec',
            'S3CompatibleStorageSpec', 'SmbStorageSpec', 'VeeamDataCloudVaultStorageSpec',
            'WasabiCloudStorageSpec', 'WindowsLocalStorageSpec']): Backup repository settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, SessionModel]]
    """

    kwargs = _get_kwargs(
        body=body,
        overwrite_owner=overwrite_owner,
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
        "AmazonS3GlacierStorageSpec",
        "AmazonS3StorageSpec",
        "AmazonSnowballEdgeStorageSpec",
        "AzureArchiveStorageSpec",
        "AzureBlobStorageSpec",
        "AzureDataBoxStorageSpec",
        "GoogleCloudStorageSpec",
        "IBMCloudStorageSpec",
        "LinuxHardenedStorageSpec",
        "LinuxLocalStorageSpec",
        "NfsStorageSpec",
        "S3CompatibleStorageSpec",
        "SmbStorageSpec",
        "VeeamDataCloudVaultStorageSpec",
        "WasabiCloudStorageSpec",
        "WindowsLocalStorageSpec",
    ],
    overwrite_owner: Union[Unset, bool] = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Optional[Union[Error, SessionModel]]:
    """Add Repository

     The HTTP POST request to the `/api/v1/backupInfrastructure/repositories` path allows you to add a
    repository to the backup infrastructure.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        overwrite_owner (Union[Unset, bool]):
        x_api_version (str):  Default: '1.3-rev0'.
        body (Union['AmazonS3GlacierStorageSpec', 'AmazonS3StorageSpec',
            'AmazonSnowballEdgeStorageSpec', 'AzureArchiveStorageSpec', 'AzureBlobStorageSpec',
            'AzureDataBoxStorageSpec', 'GoogleCloudStorageSpec', 'IBMCloudStorageSpec',
            'LinuxHardenedStorageSpec', 'LinuxLocalStorageSpec', 'NfsStorageSpec',
            'S3CompatibleStorageSpec', 'SmbStorageSpec', 'VeeamDataCloudVaultStorageSpec',
            'WasabiCloudStorageSpec', 'WindowsLocalStorageSpec']): Backup repository settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, SessionModel]
    """

    return sync_detailed(
        client=client,
        body=body,
        overwrite_owner=overwrite_owner,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        "AmazonS3GlacierStorageSpec",
        "AmazonS3StorageSpec",
        "AmazonSnowballEdgeStorageSpec",
        "AzureArchiveStorageSpec",
        "AzureBlobStorageSpec",
        "AzureDataBoxStorageSpec",
        "GoogleCloudStorageSpec",
        "IBMCloudStorageSpec",
        "LinuxHardenedStorageSpec",
        "LinuxLocalStorageSpec",
        "NfsStorageSpec",
        "S3CompatibleStorageSpec",
        "SmbStorageSpec",
        "VeeamDataCloudVaultStorageSpec",
        "WasabiCloudStorageSpec",
        "WindowsLocalStorageSpec",
    ],
    overwrite_owner: Union[Unset, bool] = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[Union[Error, SessionModel]]:
    """Add Repository

     The HTTP POST request to the `/api/v1/backupInfrastructure/repositories` path allows you to add a
    repository to the backup infrastructure.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        overwrite_owner (Union[Unset, bool]):
        x_api_version (str):  Default: '1.3-rev0'.
        body (Union['AmazonS3GlacierStorageSpec', 'AmazonS3StorageSpec',
            'AmazonSnowballEdgeStorageSpec', 'AzureArchiveStorageSpec', 'AzureBlobStorageSpec',
            'AzureDataBoxStorageSpec', 'GoogleCloudStorageSpec', 'IBMCloudStorageSpec',
            'LinuxHardenedStorageSpec', 'LinuxLocalStorageSpec', 'NfsStorageSpec',
            'S3CompatibleStorageSpec', 'SmbStorageSpec', 'VeeamDataCloudVaultStorageSpec',
            'WasabiCloudStorageSpec', 'WindowsLocalStorageSpec']): Backup repository settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, SessionModel]]
    """

    kwargs = _get_kwargs(
        body=body,
        overwrite_owner=overwrite_owner,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        "AmazonS3GlacierStorageSpec",
        "AmazonS3StorageSpec",
        "AmazonSnowballEdgeStorageSpec",
        "AzureArchiveStorageSpec",
        "AzureBlobStorageSpec",
        "AzureDataBoxStorageSpec",
        "GoogleCloudStorageSpec",
        "IBMCloudStorageSpec",
        "LinuxHardenedStorageSpec",
        "LinuxLocalStorageSpec",
        "NfsStorageSpec",
        "S3CompatibleStorageSpec",
        "SmbStorageSpec",
        "VeeamDataCloudVaultStorageSpec",
        "WasabiCloudStorageSpec",
        "WindowsLocalStorageSpec",
    ],
    overwrite_owner: Union[Unset, bool] = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Optional[Union[Error, SessionModel]]:
    """Add Repository

     The HTTP POST request to the `/api/v1/backupInfrastructure/repositories` path allows you to add a
    repository to the backup infrastructure.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        overwrite_owner (Union[Unset, bool]):
        x_api_version (str):  Default: '1.3-rev0'.
        body (Union['AmazonS3GlacierStorageSpec', 'AmazonS3StorageSpec',
            'AmazonSnowballEdgeStorageSpec', 'AzureArchiveStorageSpec', 'AzureBlobStorageSpec',
            'AzureDataBoxStorageSpec', 'GoogleCloudStorageSpec', 'IBMCloudStorageSpec',
            'LinuxHardenedStorageSpec', 'LinuxLocalStorageSpec', 'NfsStorageSpec',
            'S3CompatibleStorageSpec', 'SmbStorageSpec', 'VeeamDataCloudVaultStorageSpec',
            'WasabiCloudStorageSpec', 'WindowsLocalStorageSpec']): Backup repository settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, SessionModel]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            overwrite_owner=overwrite_owner,
            x_api_version=x_api_version,
        )
    ).parsed
