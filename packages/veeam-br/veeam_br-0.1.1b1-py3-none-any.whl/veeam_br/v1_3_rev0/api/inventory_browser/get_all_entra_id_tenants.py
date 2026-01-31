from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.e_entra_id_tenants_filters_order_column import EEntraIDTenantsFiltersOrderColumn
from ...models.entra_id_tenants_result import EntraIDTenantsResult
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, EEntraIDTenantsFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    params: dict[str, Any] = {}

    params["skip"] = skip

    params["limit"] = limit

    json_order_column: Union[Unset, str] = UNSET
    if not isinstance(order_column, Unset):
        json_order_column = order_column.value

    params["orderColumn"] = json_order_column

    params["orderAsc"] = order_asc

    params["nameFilter"] = name_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/inventory/entraId/tenants",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[EntraIDTenantsResult, Error]]:
    if response.status_code == 200:
        response_200 = EntraIDTenantsResult.from_dict(response.json())

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
) -> Response[Union[EntraIDTenantsResult, Error]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, EEntraIDTenantsFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[Union[EntraIDTenantsResult, Error]]:
    """Get All Microsoft Entra ID Tenants

     The HTTP GET request to the `/api/v1/inventory/entraId/tenants` path allows you to get an array of
    all Microsoft Entra ID tenants added to the backup server.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator Veeam Restore Operator, Veeam Tape Operator, Veeam Backup
    Viewer.</p>

    Args:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, EEntraIDTenantsFiltersOrderColumn]): Sorts Microsoft Entra ID
            tenants by one of the tenant parameters.
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[EntraIDTenantsResult, Error]]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, EEntraIDTenantsFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Optional[Union[EntraIDTenantsResult, Error]]:
    """Get All Microsoft Entra ID Tenants

     The HTTP GET request to the `/api/v1/inventory/entraId/tenants` path allows you to get an array of
    all Microsoft Entra ID tenants added to the backup server.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator Veeam Restore Operator, Veeam Tape Operator, Veeam Backup
    Viewer.</p>

    Args:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, EEntraIDTenantsFiltersOrderColumn]): Sorts Microsoft Entra ID
            tenants by one of the tenant parameters.
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[EntraIDTenantsResult, Error]
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, EEntraIDTenantsFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[Union[EntraIDTenantsResult, Error]]:
    """Get All Microsoft Entra ID Tenants

     The HTTP GET request to the `/api/v1/inventory/entraId/tenants` path allows you to get an array of
    all Microsoft Entra ID tenants added to the backup server.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator Veeam Restore Operator, Veeam Tape Operator, Veeam Backup
    Viewer.</p>

    Args:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, EEntraIDTenantsFiltersOrderColumn]): Sorts Microsoft Entra ID
            tenants by one of the tenant parameters.
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[EntraIDTenantsResult, Error]]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, EEntraIDTenantsFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Optional[Union[EntraIDTenantsResult, Error]]:
    """Get All Microsoft Entra ID Tenants

     The HTTP GET request to the `/api/v1/inventory/entraId/tenants` path allows you to get an array of
    all Microsoft Entra ID tenants added to the backup server.<p>**Available to**&#58; Veeam Backup
    Administrator, Veeam Backup Operator Veeam Restore Operator, Veeam Tape Operator, Veeam Backup
    Viewer.</p>

    Args:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, EEntraIDTenantsFiltersOrderColumn]): Sorts Microsoft Entra ID
            tenants by one of the tenant parameters.
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[EntraIDTenantsResult, Error]
    """

    return (
        await asyncio_detailed(
            client=client,
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            x_api_version=x_api_version,
        )
    ).parsed
