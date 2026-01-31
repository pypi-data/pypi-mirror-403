from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.e_proxies_filters_order_column import EProxiesFiltersOrderColumn
from ...models.e_proxy_type import EProxyType
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = UNSET,
    order_column: Union[Unset, EProxiesFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    type_filter: Union[Unset, EProxyType] = UNSET,
    host_id_filter: Union[Unset, UUID] = UNSET,
    x_api_version: str = "1.2-rev1",
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

    json_type_filter: Union[Unset, str] = UNSET
    if not isinstance(type_filter, Unset):
        json_type_filter = type_filter.value

    params["typeFilter"] = json_type_filter

    json_host_id_filter: Union[Unset, str] = UNSET
    if not isinstance(host_id_filter, Unset):
        json_host_id_filter = str(host_id_filter)
    params["hostIdFilter"] = json_host_id_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/backupInfrastructure/proxies",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Optional[Error]:
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


def _build_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Response[Error]:
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
    limit: Union[Unset, int] = UNSET,
    order_column: Union[Unset, EProxiesFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    type_filter: Union[Unset, EProxyType] = UNSET,
    host_id_filter: Union[Unset, UUID] = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[Error]:
    """Get All Proxies

     The HTTP GET request to the `/api/v1/backupInfrastructure/proxies` path allows you to get an array
    of all backup proxies that are added to the backup infrastructure.<p>**Available to**&#58; Veeam
    Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape
    Operator.</p>

    Args:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):
        order_column (Union[Unset, EProxiesFiltersOrderColumn]):
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        type_filter (Union[Unset, EProxyType]): Type of the backup proxy.
        host_id_filter (Union[Unset, UUID]):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        type_filter=type_filter,
        host_id_filter=host_id_filter,
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
    limit: Union[Unset, int] = UNSET,
    order_column: Union[Unset, EProxiesFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    type_filter: Union[Unset, EProxyType] = UNSET,
    host_id_filter: Union[Unset, UUID] = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Optional[Error]:
    """Get All Proxies

     The HTTP GET request to the `/api/v1/backupInfrastructure/proxies` path allows you to get an array
    of all backup proxies that are added to the backup infrastructure.<p>**Available to**&#58; Veeam
    Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape
    Operator.</p>

    Args:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):
        order_column (Union[Unset, EProxiesFiltersOrderColumn]):
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        type_filter (Union[Unset, EProxyType]): Type of the backup proxy.
        host_id_filter (Union[Unset, UUID]):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        type_filter=type_filter,
        host_id_filter=host_id_filter,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = UNSET,
    order_column: Union[Unset, EProxiesFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    type_filter: Union[Unset, EProxyType] = UNSET,
    host_id_filter: Union[Unset, UUID] = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Response[Error]:
    """Get All Proxies

     The HTTP GET request to the `/api/v1/backupInfrastructure/proxies` path allows you to get an array
    of all backup proxies that are added to the backup infrastructure.<p>**Available to**&#58; Veeam
    Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape
    Operator.</p>

    Args:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):
        order_column (Union[Unset, EProxiesFiltersOrderColumn]):
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        type_filter (Union[Unset, EProxyType]): Type of the backup proxy.
        host_id_filter (Union[Unset, UUID]):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        type_filter=type_filter,
        host_id_filter=host_id_filter,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = UNSET,
    order_column: Union[Unset, EProxiesFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    type_filter: Union[Unset, EProxyType] = UNSET,
    host_id_filter: Union[Unset, UUID] = UNSET,
    x_api_version: str = "1.2-rev1",
) -> Optional[Error]:
    """Get All Proxies

     The HTTP GET request to the `/api/v1/backupInfrastructure/proxies` path allows you to get an array
    of all backup proxies that are added to the backup infrastructure.<p>**Available to**&#58; Veeam
    Backup Administrator, Veeam Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape
    Operator.</p>

    Args:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):
        order_column (Union[Unset, EProxiesFiltersOrderColumn]):
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        type_filter (Union[Unset, EProxyType]): Type of the backup proxy.
        host_id_filter (Union[Unset, UUID]):
        x_api_version (str):  Default: '1.2-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error
    """

    return (
        await asyncio_detailed(
            client=client,
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            type_filter=type_filter,
            host_id_filter=host_id_filter,
            x_api_version=x_api_version,
        )
    ).parsed
