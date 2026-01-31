from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.amazon_s3_server_model import AmazonS3ServerModel
from ...models.azure_blob_server_model import AzureBlobServerModel
from ...models.error import Error
from ...models.file_server_model import FileServerModel
from ...models.nas_filer_server_model import NASFilerServerModel
from ...models.nfs_share_server_model import NFSShareServerModel
from ...models.s3_compatible_server_model import S3CompatibleServerModel
from ...models.smb_share_server_model import SMBShareServerModel
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
        "url": f"/api/v1/inventory/unstructuredDataServers/{id}",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        Error,
        Union[
            "AmazonS3ServerModel",
            "AzureBlobServerModel",
            "FileServerModel",
            "NASFilerServerModel",
            "NFSShareServerModel",
            "S3CompatibleServerModel",
            "SMBShareServerModel",
        ],
    ]
]:
    if response.status_code == 200:

        def _parse_response_200(
            data: object,
        ) -> Union[
            "AmazonS3ServerModel",
            "AzureBlobServerModel",
            "FileServerModel",
            "NASFilerServerModel",
            "NFSShareServerModel",
            "S3CompatibleServerModel",
            "SMBShareServerModel",
        ]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_unstructured_data_server_model_type_0 = FileServerModel.from_dict(data)

                return componentsschemas_unstructured_data_server_model_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_unstructured_data_server_model_type_1 = SMBShareServerModel.from_dict(data)

                return componentsschemas_unstructured_data_server_model_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_unstructured_data_server_model_type_2 = NFSShareServerModel.from_dict(data)

                return componentsschemas_unstructured_data_server_model_type_2
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_unstructured_data_server_model_type_3 = NASFilerServerModel.from_dict(data)

                return componentsschemas_unstructured_data_server_model_type_3
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_unstructured_data_server_model_type_4 = S3CompatibleServerModel.from_dict(data)

                return componentsschemas_unstructured_data_server_model_type_4
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_unstructured_data_server_model_type_5 = AmazonS3ServerModel.from_dict(data)

                return componentsschemas_unstructured_data_server_model_type_5
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_unstructured_data_server_model_type_6 = AzureBlobServerModel.from_dict(data)

            return componentsschemas_unstructured_data_server_model_type_6

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
            "AmazonS3ServerModel",
            "AzureBlobServerModel",
            "FileServerModel",
            "NASFilerServerModel",
            "NFSShareServerModel",
            "S3CompatibleServerModel",
            "SMBShareServerModel",
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
            "AmazonS3ServerModel",
            "AzureBlobServerModel",
            "FileServerModel",
            "NASFilerServerModel",
            "NFSShareServerModel",
            "S3CompatibleServerModel",
            "SMBShareServerModel",
        ],
    ]
]:
    """Get Unstructured Data Servers

     The HTTP GET request to the `/api/v1/inventory/unstructuredDataServers/{id}` path allows you to get
    an unstructured data server that has the specified `id`.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape Operator, Veeam Backup
    Viewer.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['AmazonS3ServerModel', 'AzureBlobServerModel', 'FileServerModel', 'NASFilerServerModel', 'NFSShareServerModel', 'S3CompatibleServerModel', 'SMBShareServerModel']]]
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
            "AmazonS3ServerModel",
            "AzureBlobServerModel",
            "FileServerModel",
            "NASFilerServerModel",
            "NFSShareServerModel",
            "S3CompatibleServerModel",
            "SMBShareServerModel",
        ],
    ]
]:
    """Get Unstructured Data Servers

     The HTTP GET request to the `/api/v1/inventory/unstructuredDataServers/{id}` path allows you to get
    an unstructured data server that has the specified `id`.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape Operator, Veeam Backup
    Viewer.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['AmazonS3ServerModel', 'AzureBlobServerModel', 'FileServerModel', 'NASFilerServerModel', 'NFSShareServerModel', 'S3CompatibleServerModel', 'SMBShareServerModel']]
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
            "AmazonS3ServerModel",
            "AzureBlobServerModel",
            "FileServerModel",
            "NASFilerServerModel",
            "NFSShareServerModel",
            "S3CompatibleServerModel",
            "SMBShareServerModel",
        ],
    ]
]:
    """Get Unstructured Data Servers

     The HTTP GET request to the `/api/v1/inventory/unstructuredDataServers/{id}` path allows you to get
    an unstructured data server that has the specified `id`.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape Operator, Veeam Backup
    Viewer.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['AmazonS3ServerModel', 'AzureBlobServerModel', 'FileServerModel', 'NASFilerServerModel', 'NFSShareServerModel', 'S3CompatibleServerModel', 'SMBShareServerModel']]]
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
            "AmazonS3ServerModel",
            "AzureBlobServerModel",
            "FileServerModel",
            "NASFilerServerModel",
            "NFSShareServerModel",
            "S3CompatibleServerModel",
            "SMBShareServerModel",
        ],
    ]
]:
    """Get Unstructured Data Servers

     The HTTP GET request to the `/api/v1/inventory/unstructuredDataServers/{id}` path allows you to get
    an unstructured data server that has the specified `id`.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Tape Operator, Veeam Backup
    Viewer.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['AmazonS3ServerModel', 'AzureBlobServerModel', 'FileServerModel', 'NASFilerServerModel', 'NFSShareServerModel', 'S3CompatibleServerModel', 'SMBShareServerModel']]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed
