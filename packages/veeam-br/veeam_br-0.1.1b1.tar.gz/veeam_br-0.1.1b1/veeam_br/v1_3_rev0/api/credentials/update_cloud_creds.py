from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.amazon_cloud_credentials_model import AmazonCloudCredentialsModel
from ...models.azure_compute_cloud_credentials_model import AzureComputeCloudCredentialsModel
from ...models.azure_storage_cloud_credentials_model import AzureStorageCloudCredentialsModel
from ...models.error import Error
from ...models.google_cloud_credentials_model import GoogleCloudCredentialsModel
from ...models.google_cloud_service_credentials_model import GoogleCloudServiceCredentialsModel
from ...types import Response


def _get_kwargs(
    id: UUID,
    *,
    body: Union[
        "AmazonCloudCredentialsModel",
        "AzureComputeCloudCredentialsModel",
        "AzureStorageCloudCredentialsModel",
        "GoogleCloudCredentialsModel",
        "GoogleCloudServiceCredentialsModel",
    ],
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/api/v1/cloudCredentials/{id}",
    }

    _kwargs["json"]: dict[str, Any]
    if isinstance(body, AmazonCloudCredentialsModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AzureStorageCloudCredentialsModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, AzureComputeCloudCredentialsModel):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, GoogleCloudCredentialsModel):
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
            "AmazonCloudCredentialsModel",
            "AzureComputeCloudCredentialsModel",
            "AzureStorageCloudCredentialsModel",
            "GoogleCloudCredentialsModel",
            "GoogleCloudServiceCredentialsModel",
        ],
    ]
]:
    if response.status_code == 200:

        def _parse_response_200(
            data: object,
        ) -> Union[
            "AmazonCloudCredentialsModel",
            "AzureComputeCloudCredentialsModel",
            "AzureStorageCloudCredentialsModel",
            "GoogleCloudCredentialsModel",
            "GoogleCloudServiceCredentialsModel",
        ]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_cloud_credentials_model_type_0 = AmazonCloudCredentialsModel.from_dict(data)

                return componentsschemas_cloud_credentials_model_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_cloud_credentials_model_type_1 = AzureStorageCloudCredentialsModel.from_dict(data)

                return componentsschemas_cloud_credentials_model_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_cloud_credentials_model_type_2 = AzureComputeCloudCredentialsModel.from_dict(data)

                return componentsschemas_cloud_credentials_model_type_2
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_cloud_credentials_model_type_3 = GoogleCloudCredentialsModel.from_dict(data)

                return componentsschemas_cloud_credentials_model_type_3
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_cloud_credentials_model_type_4 = GoogleCloudServiceCredentialsModel.from_dict(data)

            return componentsschemas_cloud_credentials_model_type_4

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
            "AmazonCloudCredentialsModel",
            "AzureComputeCloudCredentialsModel",
            "AzureStorageCloudCredentialsModel",
            "GoogleCloudCredentialsModel",
            "GoogleCloudServiceCredentialsModel",
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
    body: Union[
        "AmazonCloudCredentialsModel",
        "AzureComputeCloudCredentialsModel",
        "AzureStorageCloudCredentialsModel",
        "GoogleCloudCredentialsModel",
        "GoogleCloudServiceCredentialsModel",
    ],
    x_api_version: str = "1.3-rev0",
) -> Response[
    Union[
        Error,
        Union[
            "AmazonCloudCredentialsModel",
            "AzureComputeCloudCredentialsModel",
            "AzureStorageCloudCredentialsModel",
            "GoogleCloudCredentialsModel",
            "GoogleCloudServiceCredentialsModel",
        ],
    ]
]:
    """Edit Cloud Credentials Record

     The HTTP PUT request to the `/api/v1/cloudCredentials/{id}` path allows you to edit a cloud
    credentials record that has the specified `id`.<p>**Available to**&#58; Veeam Backup Administrator,
    Veeam Security Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.
        body (Union['AmazonCloudCredentialsModel', 'AzureComputeCloudCredentialsModel',
            'AzureStorageCloudCredentialsModel', 'GoogleCloudCredentialsModel',
            'GoogleCloudServiceCredentialsModel']): Cloud credential record.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['AmazonCloudCredentialsModel', 'AzureComputeCloudCredentialsModel', 'AzureStorageCloudCredentialsModel', 'GoogleCloudCredentialsModel', 'GoogleCloudServiceCredentialsModel']]]
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
        "AmazonCloudCredentialsModel",
        "AzureComputeCloudCredentialsModel",
        "AzureStorageCloudCredentialsModel",
        "GoogleCloudCredentialsModel",
        "GoogleCloudServiceCredentialsModel",
    ],
    x_api_version: str = "1.3-rev0",
) -> Optional[
    Union[
        Error,
        Union[
            "AmazonCloudCredentialsModel",
            "AzureComputeCloudCredentialsModel",
            "AzureStorageCloudCredentialsModel",
            "GoogleCloudCredentialsModel",
            "GoogleCloudServiceCredentialsModel",
        ],
    ]
]:
    """Edit Cloud Credentials Record

     The HTTP PUT request to the `/api/v1/cloudCredentials/{id}` path allows you to edit a cloud
    credentials record that has the specified `id`.<p>**Available to**&#58; Veeam Backup Administrator,
    Veeam Security Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.
        body (Union['AmazonCloudCredentialsModel', 'AzureComputeCloudCredentialsModel',
            'AzureStorageCloudCredentialsModel', 'GoogleCloudCredentialsModel',
            'GoogleCloudServiceCredentialsModel']): Cloud credential record.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['AmazonCloudCredentialsModel', 'AzureComputeCloudCredentialsModel', 'AzureStorageCloudCredentialsModel', 'GoogleCloudCredentialsModel', 'GoogleCloudServiceCredentialsModel']]
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
        "AmazonCloudCredentialsModel",
        "AzureComputeCloudCredentialsModel",
        "AzureStorageCloudCredentialsModel",
        "GoogleCloudCredentialsModel",
        "GoogleCloudServiceCredentialsModel",
    ],
    x_api_version: str = "1.3-rev0",
) -> Response[
    Union[
        Error,
        Union[
            "AmazonCloudCredentialsModel",
            "AzureComputeCloudCredentialsModel",
            "AzureStorageCloudCredentialsModel",
            "GoogleCloudCredentialsModel",
            "GoogleCloudServiceCredentialsModel",
        ],
    ]
]:
    """Edit Cloud Credentials Record

     The HTTP PUT request to the `/api/v1/cloudCredentials/{id}` path allows you to edit a cloud
    credentials record that has the specified `id`.<p>**Available to**&#58; Veeam Backup Administrator,
    Veeam Security Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.
        body (Union['AmazonCloudCredentialsModel', 'AzureComputeCloudCredentialsModel',
            'AzureStorageCloudCredentialsModel', 'GoogleCloudCredentialsModel',
            'GoogleCloudServiceCredentialsModel']): Cloud credential record.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['AmazonCloudCredentialsModel', 'AzureComputeCloudCredentialsModel', 'AzureStorageCloudCredentialsModel', 'GoogleCloudCredentialsModel', 'GoogleCloudServiceCredentialsModel']]]
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
        "AmazonCloudCredentialsModel",
        "AzureComputeCloudCredentialsModel",
        "AzureStorageCloudCredentialsModel",
        "GoogleCloudCredentialsModel",
        "GoogleCloudServiceCredentialsModel",
    ],
    x_api_version: str = "1.3-rev0",
) -> Optional[
    Union[
        Error,
        Union[
            "AmazonCloudCredentialsModel",
            "AzureComputeCloudCredentialsModel",
            "AzureStorageCloudCredentialsModel",
            "GoogleCloudCredentialsModel",
            "GoogleCloudServiceCredentialsModel",
        ],
    ]
]:
    """Edit Cloud Credentials Record

     The HTTP PUT request to the `/api/v1/cloudCredentials/{id}` path allows you to edit a cloud
    credentials record that has the specified `id`.<p>**Available to**&#58; Veeam Backup Administrator,
    Veeam Security Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.
        body (Union['AmazonCloudCredentialsModel', 'AzureComputeCloudCredentialsModel',
            'AzureStorageCloudCredentialsModel', 'GoogleCloudCredentialsModel',
            'GoogleCloudServiceCredentialsModel']): Cloud credential record.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['AmazonCloudCredentialsModel', 'AzureComputeCloudCredentialsModel', 'AzureStorageCloudCredentialsModel', 'GoogleCloudCredentialsModel', 'GoogleCloudServiceCredentialsModel']]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed
