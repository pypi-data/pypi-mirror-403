from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.amazon_ec2_browser_model import AmazonEC2BrowserModel
from ...models.amazon_ec2_browser_spec import AmazonEC2BrowserSpec
from ...models.amazon_s3_browser_model import AmazonS3BrowserModel
from ...models.amazon_s3_browser_spec import AmazonS3BrowserSpec
from ...models.amazon_snowball_edge_browser_model import AmazonSnowballEdgeBrowserModel
from ...models.amazon_snowball_edge_browser_spec import AmazonSnowballEdgeBrowserSpec
from ...models.azure_blob_browser_model import AzureBlobBrowserModel
from ...models.azure_blob_browser_spec import AzureBlobBrowserSpec
from ...models.azure_compute_browser_model import AzureComputeBrowserModel
from ...models.azure_compute_browser_spec import AzureComputeBrowserSpec
from ...models.azure_data_box_browser_model import AzureDataBoxBrowserModel
from ...models.azure_data_box_browser_spec import AzureDataBoxBrowserSpec
from ...models.error import Error
from ...models.google_cloud_storage_browser_model import GoogleCloudStorageBrowserModel
from ...models.google_cloud_storage_browser_spec import GoogleCloudStorageBrowserSpec
from ...models.ibm_cloud_storage_browser_model import IBMCloudStorageBrowserModel
from ...models.ibm_cloud_storage_browser_spec import IBMCloudStorageBrowserSpec
from ...models.s3_compatible_browser_model import S3CompatibleBrowserModel
from ...models.s3_compatible_browser_spec import S3CompatibleBrowserSpec
from ...models.wasabi_cloud_storage_browser_model import WasabiCloudStorageBrowserModel
from ...models.wasabi_cloud_storage_browser_spec import WasabiCloudStorageBrowserSpec
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: Union[
        "AmazonEC2BrowserSpec",
        "AmazonS3BrowserSpec",
        "AmazonSnowballEdgeBrowserSpec",
        "AzureBlobBrowserSpec",
        "AzureComputeBrowserSpec",
        "AzureDataBoxBrowserSpec",
        "GoogleCloudStorageBrowserSpec",
        "IBMCloudStorageBrowserSpec",
        "S3CompatibleBrowserSpec",
        "WasabiCloudStorageBrowserSpec",
    ],
    reset_cache: Union[Unset, bool] = UNSET,
    x_api_version: str = "1.2-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    params: dict[str, Any] = {}

    params["resetCache"] = reset_cache

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/cloudBrowser",
        "params": params,
    }

    _kwargs["json"]: dict[str, Any]
    if isinstance(body, AzureBlobBrowserSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AzureDataBoxBrowserSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AmazonS3BrowserSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, S3CompatibleBrowserSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AmazonSnowballEdgeBrowserSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, GoogleCloudStorageBrowserSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, IBMCloudStorageBrowserSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AzureComputeBrowserSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AmazonEC2BrowserSpec):
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
            "AmazonEC2BrowserModel",
            "AmazonS3BrowserModel",
            "AmazonSnowballEdgeBrowserModel",
            "AzureBlobBrowserModel",
            "AzureComputeBrowserModel",
            "AzureDataBoxBrowserModel",
            "GoogleCloudStorageBrowserModel",
            "IBMCloudStorageBrowserModel",
            "S3CompatibleBrowserModel",
            "WasabiCloudStorageBrowserModel",
        ],
    ]
]:
    if response.status_code == 200:

        def _parse_response_200(
            data: object,
        ) -> Union[
            "AmazonEC2BrowserModel",
            "AmazonS3BrowserModel",
            "AmazonSnowballEdgeBrowserModel",
            "AzureBlobBrowserModel",
            "AzureComputeBrowserModel",
            "AzureDataBoxBrowserModel",
            "GoogleCloudStorageBrowserModel",
            "IBMCloudStorageBrowserModel",
            "S3CompatibleBrowserModel",
            "WasabiCloudStorageBrowserModel",
        ]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_cloud_browser_model_type_0 = AzureBlobBrowserModel.from_dict(data)

                return componentsschemas_cloud_browser_model_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_cloud_browser_model_type_1 = AzureDataBoxBrowserModel.from_dict(data)

                return componentsschemas_cloud_browser_model_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_cloud_browser_model_type_2 = AmazonS3BrowserModel.from_dict(data)

                return componentsschemas_cloud_browser_model_type_2
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_cloud_browser_model_type_3 = AmazonSnowballEdgeBrowserModel.from_dict(data)

                return componentsschemas_cloud_browser_model_type_3
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_cloud_browser_model_type_4 = S3CompatibleBrowserModel.from_dict(data)

                return componentsschemas_cloud_browser_model_type_4
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_cloud_browser_model_type_5 = GoogleCloudStorageBrowserModel.from_dict(data)

                return componentsschemas_cloud_browser_model_type_5
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_cloud_browser_model_type_6 = IBMCloudStorageBrowserModel.from_dict(data)

                return componentsschemas_cloud_browser_model_type_6
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_cloud_browser_model_type_7 = AzureComputeBrowserModel.from_dict(data)

                return componentsschemas_cloud_browser_model_type_7
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_cloud_browser_model_type_8 = AmazonEC2BrowserModel.from_dict(data)

                return componentsschemas_cloud_browser_model_type_8
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_cloud_browser_model_type_9 = WasabiCloudStorageBrowserModel.from_dict(data)

            return componentsschemas_cloud_browser_model_type_9

        response_200 = _parse_response_200(response.json())

        return response_200

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
            "AmazonEC2BrowserModel",
            "AmazonS3BrowserModel",
            "AmazonSnowballEdgeBrowserModel",
            "AzureBlobBrowserModel",
            "AzureComputeBrowserModel",
            "AzureDataBoxBrowserModel",
            "GoogleCloudStorageBrowserModel",
            "IBMCloudStorageBrowserModel",
            "S3CompatibleBrowserModel",
            "WasabiCloudStorageBrowserModel",
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
        "AmazonEC2BrowserSpec",
        "AmazonS3BrowserSpec",
        "AmazonSnowballEdgeBrowserSpec",
        "AzureBlobBrowserSpec",
        "AzureComputeBrowserSpec",
        "AzureDataBoxBrowserSpec",
        "GoogleCloudStorageBrowserSpec",
        "IBMCloudStorageBrowserSpec",
        "S3CompatibleBrowserSpec",
        "WasabiCloudStorageBrowserSpec",
    ],
    reset_cache: Union[Unset, bool] = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[
    Union[
        Error,
        Union[
            "AmazonEC2BrowserModel",
            "AmazonS3BrowserModel",
            "AmazonSnowballEdgeBrowserModel",
            "AzureBlobBrowserModel",
            "AzureComputeBrowserModel",
            "AzureDataBoxBrowserModel",
            "GoogleCloudStorageBrowserModel",
            "IBMCloudStorageBrowserModel",
            "S3CompatibleBrowserModel",
            "WasabiCloudStorageBrowserModel",
        ],
    ]
]:
    """Get Cloud Hierarchy

     The HTTP POST request to the `/api/v1/cloudBrowser` path allows you to browse cloud resources
    (compute or storage) available for the specified storage account.<p>To reduce the response time and
    the number of records in the response, use `filters` if possible.</p><p>**Available to**&#58; Veeam
    Backup Administrator.</p>

    Args:
        reset_cache (Union[Unset, bool]):
        x_api_version (str):  Default: '1.2-rev1'.
        body (Union['AmazonEC2BrowserSpec', 'AmazonS3BrowserSpec',
            'AmazonSnowballEdgeBrowserSpec', 'AzureBlobBrowserSpec', 'AzureComputeBrowserSpec',
            'AzureDataBoxBrowserSpec', 'GoogleCloudStorageBrowserSpec', 'IBMCloudStorageBrowserSpec',
            'S3CompatibleBrowserSpec', 'WasabiCloudStorageBrowserSpec']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['AmazonEC2BrowserModel', 'AmazonS3BrowserModel', 'AmazonSnowballEdgeBrowserModel', 'AzureBlobBrowserModel', 'AzureComputeBrowserModel', 'AzureDataBoxBrowserModel', 'GoogleCloudStorageBrowserModel', 'IBMCloudStorageBrowserModel', 'S3CompatibleBrowserModel', 'WasabiCloudStorageBrowserModel']]]
    """

    kwargs = _get_kwargs(
        body=body,
        reset_cache=reset_cache,
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
        "AmazonEC2BrowserSpec",
        "AmazonS3BrowserSpec",
        "AmazonSnowballEdgeBrowserSpec",
        "AzureBlobBrowserSpec",
        "AzureComputeBrowserSpec",
        "AzureDataBoxBrowserSpec",
        "GoogleCloudStorageBrowserSpec",
        "IBMCloudStorageBrowserSpec",
        "S3CompatibleBrowserSpec",
        "WasabiCloudStorageBrowserSpec",
    ],
    reset_cache: Union[Unset, bool] = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Optional[
    Union[
        Error,
        Union[
            "AmazonEC2BrowserModel",
            "AmazonS3BrowserModel",
            "AmazonSnowballEdgeBrowserModel",
            "AzureBlobBrowserModel",
            "AzureComputeBrowserModel",
            "AzureDataBoxBrowserModel",
            "GoogleCloudStorageBrowserModel",
            "IBMCloudStorageBrowserModel",
            "S3CompatibleBrowserModel",
            "WasabiCloudStorageBrowserModel",
        ],
    ]
]:
    """Get Cloud Hierarchy

     The HTTP POST request to the `/api/v1/cloudBrowser` path allows you to browse cloud resources
    (compute or storage) available for the specified storage account.<p>To reduce the response time and
    the number of records in the response, use `filters` if possible.</p><p>**Available to**&#58; Veeam
    Backup Administrator.</p>

    Args:
        reset_cache (Union[Unset, bool]):
        x_api_version (str):  Default: '1.2-rev1'.
        body (Union['AmazonEC2BrowserSpec', 'AmazonS3BrowserSpec',
            'AmazonSnowballEdgeBrowserSpec', 'AzureBlobBrowserSpec', 'AzureComputeBrowserSpec',
            'AzureDataBoxBrowserSpec', 'GoogleCloudStorageBrowserSpec', 'IBMCloudStorageBrowserSpec',
            'S3CompatibleBrowserSpec', 'WasabiCloudStorageBrowserSpec']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['AmazonEC2BrowserModel', 'AmazonS3BrowserModel', 'AmazonSnowballEdgeBrowserModel', 'AzureBlobBrowserModel', 'AzureComputeBrowserModel', 'AzureDataBoxBrowserModel', 'GoogleCloudStorageBrowserModel', 'IBMCloudStorageBrowserModel', 'S3CompatibleBrowserModel', 'WasabiCloudStorageBrowserModel']]
    """

    return sync_detailed(
        client=client,
        body=body,
        reset_cache=reset_cache,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        "AmazonEC2BrowserSpec",
        "AmazonS3BrowserSpec",
        "AmazonSnowballEdgeBrowserSpec",
        "AzureBlobBrowserSpec",
        "AzureComputeBrowserSpec",
        "AzureDataBoxBrowserSpec",
        "GoogleCloudStorageBrowserSpec",
        "IBMCloudStorageBrowserSpec",
        "S3CompatibleBrowserSpec",
        "WasabiCloudStorageBrowserSpec",
    ],
    reset_cache: Union[Unset, bool] = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[
    Union[
        Error,
        Union[
            "AmazonEC2BrowserModel",
            "AmazonS3BrowserModel",
            "AmazonSnowballEdgeBrowserModel",
            "AzureBlobBrowserModel",
            "AzureComputeBrowserModel",
            "AzureDataBoxBrowserModel",
            "GoogleCloudStorageBrowserModel",
            "IBMCloudStorageBrowserModel",
            "S3CompatibleBrowserModel",
            "WasabiCloudStorageBrowserModel",
        ],
    ]
]:
    """Get Cloud Hierarchy

     The HTTP POST request to the `/api/v1/cloudBrowser` path allows you to browse cloud resources
    (compute or storage) available for the specified storage account.<p>To reduce the response time and
    the number of records in the response, use `filters` if possible.</p><p>**Available to**&#58; Veeam
    Backup Administrator.</p>

    Args:
        reset_cache (Union[Unset, bool]):
        x_api_version (str):  Default: '1.2-rev1'.
        body (Union['AmazonEC2BrowserSpec', 'AmazonS3BrowserSpec',
            'AmazonSnowballEdgeBrowserSpec', 'AzureBlobBrowserSpec', 'AzureComputeBrowserSpec',
            'AzureDataBoxBrowserSpec', 'GoogleCloudStorageBrowserSpec', 'IBMCloudStorageBrowserSpec',
            'S3CompatibleBrowserSpec', 'WasabiCloudStorageBrowserSpec']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['AmazonEC2BrowserModel', 'AmazonS3BrowserModel', 'AmazonSnowballEdgeBrowserModel', 'AzureBlobBrowserModel', 'AzureComputeBrowserModel', 'AzureDataBoxBrowserModel', 'GoogleCloudStorageBrowserModel', 'IBMCloudStorageBrowserModel', 'S3CompatibleBrowserModel', 'WasabiCloudStorageBrowserModel']]]
    """

    kwargs = _get_kwargs(
        body=body,
        reset_cache=reset_cache,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        "AmazonEC2BrowserSpec",
        "AmazonS3BrowserSpec",
        "AmazonSnowballEdgeBrowserSpec",
        "AzureBlobBrowserSpec",
        "AzureComputeBrowserSpec",
        "AzureDataBoxBrowserSpec",
        "GoogleCloudStorageBrowserSpec",
        "IBMCloudStorageBrowserSpec",
        "S3CompatibleBrowserSpec",
        "WasabiCloudStorageBrowserSpec",
    ],
    reset_cache: Union[Unset, bool] = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Optional[
    Union[
        Error,
        Union[
            "AmazonEC2BrowserModel",
            "AmazonS3BrowserModel",
            "AmazonSnowballEdgeBrowserModel",
            "AzureBlobBrowserModel",
            "AzureComputeBrowserModel",
            "AzureDataBoxBrowserModel",
            "GoogleCloudStorageBrowserModel",
            "IBMCloudStorageBrowserModel",
            "S3CompatibleBrowserModel",
            "WasabiCloudStorageBrowserModel",
        ],
    ]
]:
    """Get Cloud Hierarchy

     The HTTP POST request to the `/api/v1/cloudBrowser` path allows you to browse cloud resources
    (compute or storage) available for the specified storage account.<p>To reduce the response time and
    the number of records in the response, use `filters` if possible.</p><p>**Available to**&#58; Veeam
    Backup Administrator.</p>

    Args:
        reset_cache (Union[Unset, bool]):
        x_api_version (str):  Default: '1.2-rev1'.
        body (Union['AmazonEC2BrowserSpec', 'AmazonS3BrowserSpec',
            'AmazonSnowballEdgeBrowserSpec', 'AzureBlobBrowserSpec', 'AzureComputeBrowserSpec',
            'AzureDataBoxBrowserSpec', 'GoogleCloudStorageBrowserSpec', 'IBMCloudStorageBrowserSpec',
            'S3CompatibleBrowserSpec', 'WasabiCloudStorageBrowserSpec']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['AmazonEC2BrowserModel', 'AmazonS3BrowserModel', 'AmazonSnowballEdgeBrowserModel', 'AzureBlobBrowserModel', 'AzureComputeBrowserModel', 'AzureDataBoxBrowserModel', 'GoogleCloudStorageBrowserModel', 'IBMCloudStorageBrowserModel', 'S3CompatibleBrowserModel', 'WasabiCloudStorageBrowserModel']]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            reset_cache=reset_cache,
            x_api_version=x_api_version,
        )
    ).parsed
