from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.e_instance_workloads_filters_order_column import EInstanceWorkloadsFiltersOrderColumn
from ...models.error import Error
from ...models.instance_license_workload_result import InstanceLicenseWorkloadResult
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, EInstanceWorkloadsFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    host_name_filter: Union[Unset, str] = UNSET,
    used_instances_number_filter: Union[Unset, float] = UNSET,
    type_filter: Union[Unset, str] = UNSET,
    instance_id_filter: Union[Unset, UUID] = UNSET,
    x_api_version: str = "1.3-rev1",
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

    params["hostNameFilter"] = host_name_filter

    params["usedInstancesNumberFilter"] = used_instances_number_filter

    params["typeFilter"] = type_filter

    json_instance_id_filter: Union[Unset, str] = UNSET
    if not isinstance(instance_id_filter, Unset):
        json_instance_id_filter = str(instance_id_filter)
    params["instanceIdFilter"] = json_instance_id_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/license/instances",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, InstanceLicenseWorkloadResult]]:
    if response.status_code == 200:
        response_200 = InstanceLicenseWorkloadResult.from_dict(response.json())

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
) -> Response[Union[Error, InstanceLicenseWorkloadResult]]:
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
    order_column: Union[Unset, EInstanceWorkloadsFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    host_name_filter: Union[Unset, str] = UNSET,
    used_instances_number_filter: Union[Unset, float] = UNSET,
    type_filter: Union[Unset, str] = UNSET,
    instance_id_filter: Union[Unset, UUID] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[Union[Error, InstanceLicenseWorkloadResult]]:
    """Get Instance Licenses Consumption

     The HTTP GET request to the `/api/v1/license/instances` endpoint gets information about instance
    license consumption on the backup server.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, EInstanceWorkloadsFiltersOrderColumn]): Sorts licensed
            workloads according to one of the parameters.
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        host_name_filter (Union[Unset, str]):
        used_instances_number_filter (Union[Unset, float]):
        type_filter (Union[Unset, str]):
        instance_id_filter (Union[Unset, UUID]):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, InstanceLicenseWorkloadResult]]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        host_name_filter=host_name_filter,
        used_instances_number_filter=used_instances_number_filter,
        type_filter=type_filter,
        instance_id_filter=instance_id_filter,
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
    order_column: Union[Unset, EInstanceWorkloadsFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    host_name_filter: Union[Unset, str] = UNSET,
    used_instances_number_filter: Union[Unset, float] = UNSET,
    type_filter: Union[Unset, str] = UNSET,
    instance_id_filter: Union[Unset, UUID] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[Error, InstanceLicenseWorkloadResult]]:
    """Get Instance Licenses Consumption

     The HTTP GET request to the `/api/v1/license/instances` endpoint gets information about instance
    license consumption on the backup server.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, EInstanceWorkloadsFiltersOrderColumn]): Sorts licensed
            workloads according to one of the parameters.
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        host_name_filter (Union[Unset, str]):
        used_instances_number_filter (Union[Unset, float]):
        type_filter (Union[Unset, str]):
        instance_id_filter (Union[Unset, UUID]):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, InstanceLicenseWorkloadResult]
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        host_name_filter=host_name_filter,
        used_instances_number_filter=used_instances_number_filter,
        type_filter=type_filter,
        instance_id_filter=instance_id_filter,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, EInstanceWorkloadsFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    host_name_filter: Union[Unset, str] = UNSET,
    used_instances_number_filter: Union[Unset, float] = UNSET,
    type_filter: Union[Unset, str] = UNSET,
    instance_id_filter: Union[Unset, UUID] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[Union[Error, InstanceLicenseWorkloadResult]]:
    """Get Instance Licenses Consumption

     The HTTP GET request to the `/api/v1/license/instances` endpoint gets information about instance
    license consumption on the backup server.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, EInstanceWorkloadsFiltersOrderColumn]): Sorts licensed
            workloads according to one of the parameters.
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        host_name_filter (Union[Unset, str]):
        used_instances_number_filter (Union[Unset, float]):
        type_filter (Union[Unset, str]):
        instance_id_filter (Union[Unset, UUID]):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, InstanceLicenseWorkloadResult]]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        host_name_filter=host_name_filter,
        used_instances_number_filter=used_instances_number_filter,
        type_filter=type_filter,
        instance_id_filter=instance_id_filter,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, EInstanceWorkloadsFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    host_name_filter: Union[Unset, str] = UNSET,
    used_instances_number_filter: Union[Unset, float] = UNSET,
    type_filter: Union[Unset, str] = UNSET,
    instance_id_filter: Union[Unset, UUID] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[Error, InstanceLicenseWorkloadResult]]:
    """Get Instance Licenses Consumption

     The HTTP GET request to the `/api/v1/license/instances` endpoint gets information about instance
    license consumption on the backup server.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, EInstanceWorkloadsFiltersOrderColumn]): Sorts licensed
            workloads according to one of the parameters.
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        host_name_filter (Union[Unset, str]):
        used_instances_number_filter (Union[Unset, float]):
        type_filter (Union[Unset, str]):
        instance_id_filter (Union[Unset, UUID]):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, InstanceLicenseWorkloadResult]
    """

    return (
        await asyncio_detailed(
            client=client,
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            host_name_filter=host_name_filter,
            used_instances_number_filter=used_instances_number_filter,
            type_filter=type_filter,
            instance_id_filter=instance_id_filter,
            x_api_version=x_api_version,
        )
    ).parsed
