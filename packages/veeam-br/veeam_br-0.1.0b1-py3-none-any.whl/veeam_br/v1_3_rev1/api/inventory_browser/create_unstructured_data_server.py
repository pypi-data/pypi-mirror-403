from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.amazon_s3_server_spec import AmazonS3ServerSpec
from ...models.azure_blob_server_spec import AzureBlobServerSpec
from ...models.error import Error
from ...models.file_server_spec import FileServerSpec
from ...models.nas_filer_server_spec import NASFilerServerSpec
from ...models.nfs_share_server_spec import NFSShareServerSpec
from ...models.s3_compatible_server_spec import S3CompatibleServerSpec
from ...models.session_model import SessionModel
from ...models.smb_share_server_spec import SMBShareServerSpec
from ...types import Response


def _get_kwargs(
    *,
    body: Union[
        "AmazonS3ServerSpec",
        "AzureBlobServerSpec",
        "FileServerSpec",
        "NASFilerServerSpec",
        "NFSShareServerSpec",
        "S3CompatibleServerSpec",
        "SMBShareServerSpec",
    ],
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/inventory/unstructuredDataServers",
    }

    _kwargs["json"]: dict[str, Any]
    if isinstance(body, FileServerSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, SMBShareServerSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, NFSShareServerSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, NASFilerServerSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, S3CompatibleServerSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AmazonS3ServerSpec):
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
        "AmazonS3ServerSpec",
        "AzureBlobServerSpec",
        "FileServerSpec",
        "NASFilerServerSpec",
        "NFSShareServerSpec",
        "S3CompatibleServerSpec",
        "SMBShareServerSpec",
    ],
    x_api_version: str = "1.3-rev1",
) -> Response[Union[Error, SessionModel]]:
    """Add Unstructured Data Servers

     The HTTP POST request to the `/api/v1/inventory/unstructuredDataServers` endpoint adds unstructured
    data servers to the backup server.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (Union['AmazonS3ServerSpec', 'AzureBlobServerSpec', 'FileServerSpec',
            'NASFilerServerSpec', 'NFSShareServerSpec', 'S3CompatibleServerSpec',
            'SMBShareServerSpec']): Settings for unstructured data server.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, SessionModel]]
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
        "AmazonS3ServerSpec",
        "AzureBlobServerSpec",
        "FileServerSpec",
        "NASFilerServerSpec",
        "NFSShareServerSpec",
        "S3CompatibleServerSpec",
        "SMBShareServerSpec",
    ],
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[Error, SessionModel]]:
    """Add Unstructured Data Servers

     The HTTP POST request to the `/api/v1/inventory/unstructuredDataServers` endpoint adds unstructured
    data servers to the backup server.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (Union['AmazonS3ServerSpec', 'AzureBlobServerSpec', 'FileServerSpec',
            'NASFilerServerSpec', 'NFSShareServerSpec', 'S3CompatibleServerSpec',
            'SMBShareServerSpec']): Settings for unstructured data server.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, SessionModel]
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
        "AmazonS3ServerSpec",
        "AzureBlobServerSpec",
        "FileServerSpec",
        "NASFilerServerSpec",
        "NFSShareServerSpec",
        "S3CompatibleServerSpec",
        "SMBShareServerSpec",
    ],
    x_api_version: str = "1.3-rev1",
) -> Response[Union[Error, SessionModel]]:
    """Add Unstructured Data Servers

     The HTTP POST request to the `/api/v1/inventory/unstructuredDataServers` endpoint adds unstructured
    data servers to the backup server.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (Union['AmazonS3ServerSpec', 'AzureBlobServerSpec', 'FileServerSpec',
            'NASFilerServerSpec', 'NFSShareServerSpec', 'S3CompatibleServerSpec',
            'SMBShareServerSpec']): Settings for unstructured data server.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, SessionModel]]
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
        "AmazonS3ServerSpec",
        "AzureBlobServerSpec",
        "FileServerSpec",
        "NASFilerServerSpec",
        "NFSShareServerSpec",
        "S3CompatibleServerSpec",
        "SMBShareServerSpec",
    ],
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[Error, SessionModel]]:
    """Add Unstructured Data Servers

     The HTTP POST request to the `/api/v1/inventory/unstructuredDataServers` endpoint adds unstructured
    data servers to the backup server.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (Union['AmazonS3ServerSpec', 'AzureBlobServerSpec', 'FileServerSpec',
            'NASFilerServerSpec', 'NFSShareServerSpec', 'S3CompatibleServerSpec',
            'SMBShareServerSpec']): Settings for unstructured data server.

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
            x_api_version=x_api_version,
        )
    ).parsed
