from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.amazon_s3_browser_destination_spec import AmazonS3BrowserDestinationSpec
from ...models.amazon_snowball_edge_browser_destination_spec import AmazonSnowballEdgeBrowserDestinationSpec
from ...models.azure_blob_browser_destination_spec import AzureBlobBrowserDestinationSpec
from ...models.azure_data_box_browser_destination_spec import AzureDataBoxBrowserDestinationSpec
from ...models.empty_success_response import EmptySuccessResponse
from ...models.error import Error
from ...models.google_cloud_storage_browser_destination_spec import GoogleCloudStorageBrowserDestinationSpec
from ...models.ibm_cloud_storage_browser_destination_spec import IBMCloudStorageBrowserDestinationSpec
from ...models.s3_compatible_browser_destination_spec import S3CompatibleBrowserDestinationSpec
from ...models.veeam_data_cloud_vault_browser_destination_spec import VeeamDataCloudVaultBrowserDestinationSpec
from ...models.wasabi_cloud_storage_browser_destination_spec import WasabiCloudStorageBrowserDestinationSpec
from ...types import Response


def _get_kwargs(
    *,
    body: Union[
        "AmazonS3BrowserDestinationSpec",
        "AmazonSnowballEdgeBrowserDestinationSpec",
        "AzureBlobBrowserDestinationSpec",
        "AzureDataBoxBrowserDestinationSpec",
        "GoogleCloudStorageBrowserDestinationSpec",
        "IBMCloudStorageBrowserDestinationSpec",
        "S3CompatibleBrowserDestinationSpec",
        "VeeamDataCloudVaultBrowserDestinationSpec",
        "WasabiCloudStorageBrowserDestinationSpec",
    ],
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/cloudBrowser/newFolder",
    }

    _kwargs["json"]: dict[str, Any]
    if isinstance(body, AzureBlobBrowserDestinationSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AzureDataBoxBrowserDestinationSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AmazonS3BrowserDestinationSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, S3CompatibleBrowserDestinationSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AmazonSnowballEdgeBrowserDestinationSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, GoogleCloudStorageBrowserDestinationSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, IBMCloudStorageBrowserDestinationSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, WasabiCloudStorageBrowserDestinationSpec):
        _kwargs["json"] = body.to_dict()
    else:
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[EmptySuccessResponse, Error]]:
    if response.status_code == 201:
        response_201 = EmptySuccessResponse.from_dict(response.json())

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
) -> Response[Union[EmptySuccessResponse, Error]]:
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
        "AmazonS3BrowserDestinationSpec",
        "AmazonSnowballEdgeBrowserDestinationSpec",
        "AzureBlobBrowserDestinationSpec",
        "AzureDataBoxBrowserDestinationSpec",
        "GoogleCloudStorageBrowserDestinationSpec",
        "IBMCloudStorageBrowserDestinationSpec",
        "S3CompatibleBrowserDestinationSpec",
        "VeeamDataCloudVaultBrowserDestinationSpec",
        "WasabiCloudStorageBrowserDestinationSpec",
    ],
    x_api_version: str = "1.3-rev0",
) -> Response[Union[EmptySuccessResponse, Error]]:
    r"""Create New Cloud Storage Folder

     The HTTP POST request to the `/api/v1/cloudBrowser/newFolder` path allows you to create a new folder
    in the cloud infrastructure.<p>**Available to**&#58; Veeam Backup Administrator.</p><div
    class=\"note\"><strong>NOTE</strong><br>The REST API does not create new containers, you can create
    a folder in an existing container only.</div>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (Union['AmazonS3BrowserDestinationSpec', 'AmazonSnowballEdgeBrowserDestinationSpec',
            'AzureBlobBrowserDestinationSpec', 'AzureDataBoxBrowserDestinationSpec',
            'GoogleCloudStorageBrowserDestinationSpec', 'IBMCloudStorageBrowserDestinationSpec',
            'S3CompatibleBrowserDestinationSpec', 'VeeamDataCloudVaultBrowserDestinationSpec',
            'WasabiCloudStorageBrowserDestinationSpec']): Settings for creating new folder in storage.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[EmptySuccessResponse, Error]]
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
        "AmazonS3BrowserDestinationSpec",
        "AmazonSnowballEdgeBrowserDestinationSpec",
        "AzureBlobBrowserDestinationSpec",
        "AzureDataBoxBrowserDestinationSpec",
        "GoogleCloudStorageBrowserDestinationSpec",
        "IBMCloudStorageBrowserDestinationSpec",
        "S3CompatibleBrowserDestinationSpec",
        "VeeamDataCloudVaultBrowserDestinationSpec",
        "WasabiCloudStorageBrowserDestinationSpec",
    ],
    x_api_version: str = "1.3-rev0",
) -> Optional[Union[EmptySuccessResponse, Error]]:
    r"""Create New Cloud Storage Folder

     The HTTP POST request to the `/api/v1/cloudBrowser/newFolder` path allows you to create a new folder
    in the cloud infrastructure.<p>**Available to**&#58; Veeam Backup Administrator.</p><div
    class=\"note\"><strong>NOTE</strong><br>The REST API does not create new containers, you can create
    a folder in an existing container only.</div>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (Union['AmazonS3BrowserDestinationSpec', 'AmazonSnowballEdgeBrowserDestinationSpec',
            'AzureBlobBrowserDestinationSpec', 'AzureDataBoxBrowserDestinationSpec',
            'GoogleCloudStorageBrowserDestinationSpec', 'IBMCloudStorageBrowserDestinationSpec',
            'S3CompatibleBrowserDestinationSpec', 'VeeamDataCloudVaultBrowserDestinationSpec',
            'WasabiCloudStorageBrowserDestinationSpec']): Settings for creating new folder in storage.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[EmptySuccessResponse, Error]
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
        "AmazonS3BrowserDestinationSpec",
        "AmazonSnowballEdgeBrowserDestinationSpec",
        "AzureBlobBrowserDestinationSpec",
        "AzureDataBoxBrowserDestinationSpec",
        "GoogleCloudStorageBrowserDestinationSpec",
        "IBMCloudStorageBrowserDestinationSpec",
        "S3CompatibleBrowserDestinationSpec",
        "VeeamDataCloudVaultBrowserDestinationSpec",
        "WasabiCloudStorageBrowserDestinationSpec",
    ],
    x_api_version: str = "1.3-rev0",
) -> Response[Union[EmptySuccessResponse, Error]]:
    r"""Create New Cloud Storage Folder

     The HTTP POST request to the `/api/v1/cloudBrowser/newFolder` path allows you to create a new folder
    in the cloud infrastructure.<p>**Available to**&#58; Veeam Backup Administrator.</p><div
    class=\"note\"><strong>NOTE</strong><br>The REST API does not create new containers, you can create
    a folder in an existing container only.</div>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (Union['AmazonS3BrowserDestinationSpec', 'AmazonSnowballEdgeBrowserDestinationSpec',
            'AzureBlobBrowserDestinationSpec', 'AzureDataBoxBrowserDestinationSpec',
            'GoogleCloudStorageBrowserDestinationSpec', 'IBMCloudStorageBrowserDestinationSpec',
            'S3CompatibleBrowserDestinationSpec', 'VeeamDataCloudVaultBrowserDestinationSpec',
            'WasabiCloudStorageBrowserDestinationSpec']): Settings for creating new folder in storage.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[EmptySuccessResponse, Error]]
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
        "AmazonS3BrowserDestinationSpec",
        "AmazonSnowballEdgeBrowserDestinationSpec",
        "AzureBlobBrowserDestinationSpec",
        "AzureDataBoxBrowserDestinationSpec",
        "GoogleCloudStorageBrowserDestinationSpec",
        "IBMCloudStorageBrowserDestinationSpec",
        "S3CompatibleBrowserDestinationSpec",
        "VeeamDataCloudVaultBrowserDestinationSpec",
        "WasabiCloudStorageBrowserDestinationSpec",
    ],
    x_api_version: str = "1.3-rev0",
) -> Optional[Union[EmptySuccessResponse, Error]]:
    r"""Create New Cloud Storage Folder

     The HTTP POST request to the `/api/v1/cloudBrowser/newFolder` path allows you to create a new folder
    in the cloud infrastructure.<p>**Available to**&#58; Veeam Backup Administrator.</p><div
    class=\"note\"><strong>NOTE</strong><br>The REST API does not create new containers, you can create
    a folder in an existing container only.</div>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (Union['AmazonS3BrowserDestinationSpec', 'AmazonSnowballEdgeBrowserDestinationSpec',
            'AzureBlobBrowserDestinationSpec', 'AzureDataBoxBrowserDestinationSpec',
            'GoogleCloudStorageBrowserDestinationSpec', 'IBMCloudStorageBrowserDestinationSpec',
            'S3CompatibleBrowserDestinationSpec', 'VeeamDataCloudVaultBrowserDestinationSpec',
            'WasabiCloudStorageBrowserDestinationSpec']): Settings for creating new folder in storage.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[EmptySuccessResponse, Error]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed
