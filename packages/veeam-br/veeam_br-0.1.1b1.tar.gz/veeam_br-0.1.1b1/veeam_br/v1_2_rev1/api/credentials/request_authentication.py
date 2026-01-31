from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.google_cloud_compute_verification_code_model import GoogleCloudComputeVerificationCodeModel
from ...types import Response


def _get_kwargs(
    *,
    x_api_version: str = "1.2-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/cloudCredentials/authenticate",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, GoogleCloudComputeVerificationCodeModel]]:
    if response.status_code == 201:
        response_201 = GoogleCloudComputeVerificationCodeModel.from_dict(response.json())

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
) -> Response[Union[Error, GoogleCloudComputeVerificationCodeModel]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.2-rev1",
) -> Response[Union[Error, GoogleCloudComputeVerificationCodeModel]]:
    """Get Google Authentication Information

     The HTTP POST request to the `/api/v1/cloudCredentials/authenticate` path allows you to get
    authentication information required to sign in to Google Cloud.<p> **Available to**&#58; Veeam
    Backup Administrator, Veeam Security Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, GoogleCloudComputeVerificationCodeModel]]
    """

    kwargs = _get_kwargs(
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.2-rev1",
) -> Optional[Union[Error, GoogleCloudComputeVerificationCodeModel]]:
    """Get Google Authentication Information

     The HTTP POST request to the `/api/v1/cloudCredentials/authenticate` path allows you to get
    authentication information required to sign in to Google Cloud.<p> **Available to**&#58; Veeam
    Backup Administrator, Veeam Security Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, GoogleCloudComputeVerificationCodeModel]
    """

    return sync_detailed(
        client=client,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.2-rev1",
) -> Response[Union[Error, GoogleCloudComputeVerificationCodeModel]]:
    """Get Google Authentication Information

     The HTTP POST request to the `/api/v1/cloudCredentials/authenticate` path allows you to get
    authentication information required to sign in to Google Cloud.<p> **Available to**&#58; Veeam
    Backup Administrator, Veeam Security Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, GoogleCloudComputeVerificationCodeModel]]
    """

    kwargs = _get_kwargs(
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.2-rev1",
) -> Optional[Union[Error, GoogleCloudComputeVerificationCodeModel]]:
    """Get Google Authentication Information

     The HTTP POST request to the `/api/v1/cloudCredentials/authenticate` path allows you to get
    authentication information required to sign in to Google Cloud.<p> **Available to**&#58; Veeam
    Backup Administrator, Veeam Security Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, GoogleCloudComputeVerificationCodeModel]
    """

    return (
        await asyncio_detailed(
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed
