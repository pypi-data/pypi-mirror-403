from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.capacity_license_workload_result import CapacityLicenseWorkloadResult
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    *,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/license/capacity",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[CapacityLicenseWorkloadResult, Error]]:
    if response.status_code == 200:
        response_200 = CapacityLicenseWorkloadResult.from_dict(response.json())

        return response_200

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
) -> Response[Union[CapacityLicenseWorkloadResult, Error]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev0",
) -> Response[Union[CapacityLicenseWorkloadResult, Error]]:
    """Get Capacity License Consumption

     The HTTP GET request to the `/api/v1/license/capacity` path allows you to get information about the
    capacity license instance consumption by file shares and object storages. <p>**Available to**&#58;
    Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CapacityLicenseWorkloadResult, Error]]
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
    x_api_version: str = "1.3-rev0",
) -> Optional[Union[CapacityLicenseWorkloadResult, Error]]:
    """Get Capacity License Consumption

     The HTTP GET request to the `/api/v1/license/capacity` path allows you to get information about the
    capacity license instance consumption by file shares and object storages. <p>**Available to**&#58;
    Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CapacityLicenseWorkloadResult, Error]
    """

    return sync_detailed(
        client=client,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev0",
) -> Response[Union[CapacityLicenseWorkloadResult, Error]]:
    """Get Capacity License Consumption

     The HTTP GET request to the `/api/v1/license/capacity` path allows you to get information about the
    capacity license instance consumption by file shares and object storages. <p>**Available to**&#58;
    Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CapacityLicenseWorkloadResult, Error]]
    """

    kwargs = _get_kwargs(
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev0",
) -> Optional[Union[CapacityLicenseWorkloadResult, Error]]:
    """Get Capacity License Consumption

     The HTTP GET request to the `/api/v1/license/capacity` path allows you to get information about the
    capacity license instance consumption by file shares and object storages. <p>**Available to**&#58;
    Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CapacityLicenseWorkloadResult, Error]
    """

    return (
        await asyncio_detailed(
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed
