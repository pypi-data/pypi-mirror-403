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
from ...models.smb_storage_model import SmbStorageModel
from ...models.veeam_data_cloud_vault_storage_model import VeeamDataCloudVaultStorageModel
from ...models.wasabi_cloud_storage_model import WasabiCloudStorageModel
from ...models.windows_local_storage_model import WindowsLocalStorageModel
from ...types import Response


def _get_kwargs(
    id: UUID,
    *,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/backupInfrastructure/repositories/{id}",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        Error,
        Union[
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
    ]
]:
    if response.status_code == 200:

        def _parse_response_200(
            data: object,
        ) -> Union[
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
        ]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_repository_model_type_0 = WindowsLocalStorageModel.from_dict(data)

                return componentsschemas_repository_model_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_repository_model_type_1 = LinuxLocalStorageModel.from_dict(data)

                return componentsschemas_repository_model_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_repository_model_type_2 = NfsStorageModel.from_dict(data)

                return componentsschemas_repository_model_type_2
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_repository_model_type_3 = SmbStorageModel.from_dict(data)

                return componentsschemas_repository_model_type_3
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_repository_model_type_4 = AzureBlobStorageModel.from_dict(data)

                return componentsschemas_repository_model_type_4
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_repository_model_type_5 = AzureDataBoxStorageModel.from_dict(data)

                return componentsschemas_repository_model_type_5
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_repository_model_type_6 = AmazonS3StorageModel.from_dict(data)

                return componentsschemas_repository_model_type_6
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_repository_model_type_7 = AmazonSnowballEdgeStorageModel.from_dict(data)

                return componentsschemas_repository_model_type_7
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_repository_model_type_8 = S3CompatibleStorageModel.from_dict(data)

                return componentsschemas_repository_model_type_8
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_repository_model_type_9 = GoogleCloudStorageModel.from_dict(data)

                return componentsschemas_repository_model_type_9
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_repository_model_type_10 = IBMCloudStorageModel.from_dict(data)

                return componentsschemas_repository_model_type_10
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_repository_model_type_11 = AmazonS3GlacierStorageModel.from_dict(data)

                return componentsschemas_repository_model_type_11
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_repository_model_type_12 = AzureArchiveStorageModel.from_dict(data)

                return componentsschemas_repository_model_type_12
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_repository_model_type_13 = WasabiCloudStorageModel.from_dict(data)

                return componentsschemas_repository_model_type_13
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_repository_model_type_14 = LinuxHardenedStorageModel.from_dict(data)

                return componentsschemas_repository_model_type_14
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_repository_model_type_15 = VeeamDataCloudVaultStorageModel.from_dict(data)

            return componentsschemas_repository_model_type_15

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
    x_api_version: str = "1.3-rev1",
) -> Response[
    Union[
        Error,
        Union[
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
    ]
]:
    """Get Repository

     The HTTP GET request to the `/api/v1/backupInfrastructure/repositories/{id}` endpoint gets a backup
    repository that has the specified `id`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['AmazonS3GlacierStorageModel', 'AmazonS3StorageModel', 'AmazonSnowballEdgeStorageModel', 'AzureArchiveStorageModel', 'AzureBlobStorageModel', 'AzureDataBoxStorageModel', 'GoogleCloudStorageModel', 'IBMCloudStorageModel', 'LinuxHardenedStorageModel', 'LinuxLocalStorageModel', 'NfsStorageModel', 'S3CompatibleStorageModel', 'SmbStorageModel', 'VeeamDataCloudVaultStorageModel', 'WasabiCloudStorageModel', 'WindowsLocalStorageModel']]]
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
    x_api_version: str = "1.3-rev1",
) -> Optional[
    Union[
        Error,
        Union[
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
    ]
]:
    """Get Repository

     The HTTP GET request to the `/api/v1/backupInfrastructure/repositories/{id}` endpoint gets a backup
    repository that has the specified `id`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['AmazonS3GlacierStorageModel', 'AmazonS3StorageModel', 'AmazonSnowballEdgeStorageModel', 'AzureArchiveStorageModel', 'AzureBlobStorageModel', 'AzureDataBoxStorageModel', 'GoogleCloudStorageModel', 'IBMCloudStorageModel', 'LinuxHardenedStorageModel', 'LinuxLocalStorageModel', 'NfsStorageModel', 'S3CompatibleStorageModel', 'SmbStorageModel', 'VeeamDataCloudVaultStorageModel', 'WasabiCloudStorageModel', 'WindowsLocalStorageModel']]
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
    x_api_version: str = "1.3-rev1",
) -> Response[
    Union[
        Error,
        Union[
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
    ]
]:
    """Get Repository

     The HTTP GET request to the `/api/v1/backupInfrastructure/repositories/{id}` endpoint gets a backup
    repository that has the specified `id`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['AmazonS3GlacierStorageModel', 'AmazonS3StorageModel', 'AmazonSnowballEdgeStorageModel', 'AzureArchiveStorageModel', 'AzureBlobStorageModel', 'AzureDataBoxStorageModel', 'GoogleCloudStorageModel', 'IBMCloudStorageModel', 'LinuxHardenedStorageModel', 'LinuxLocalStorageModel', 'NfsStorageModel', 'S3CompatibleStorageModel', 'SmbStorageModel', 'VeeamDataCloudVaultStorageModel', 'WasabiCloudStorageModel', 'WindowsLocalStorageModel']]]
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
    x_api_version: str = "1.3-rev1",
) -> Optional[
    Union[
        Error,
        Union[
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
    ]
]:
    """Get Repository

     The HTTP GET request to the `/api/v1/backupInfrastructure/repositories/{id}` endpoint gets a backup
    repository that has the specified `id`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['AmazonS3GlacierStorageModel', 'AmazonS3StorageModel', 'AmazonSnowballEdgeStorageModel', 'AzureArchiveStorageModel', 'AzureBlobStorageModel', 'AzureDataBoxStorageModel', 'GoogleCloudStorageModel', 'IBMCloudStorageModel', 'LinuxHardenedStorageModel', 'LinuxLocalStorageModel', 'NfsStorageModel', 'S3CompatibleStorageModel', 'SmbStorageModel', 'VeeamDataCloudVaultStorageModel', 'WasabiCloudStorageModel', 'WindowsLocalStorageModel']]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed
