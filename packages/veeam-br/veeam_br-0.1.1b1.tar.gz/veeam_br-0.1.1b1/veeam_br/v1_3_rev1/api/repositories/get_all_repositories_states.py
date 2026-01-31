from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.e_repository_states_filters_order_column import ERepositoryStatesFiltersOrderColumn
from ...models.e_repository_type import ERepositoryType
from ...models.e_scale_out_repository_extent_type import EScaleOutRepositoryExtentType
from ...models.error import Error
from ...models.repository_states_result import RepositoryStatesResult
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, ERepositoryStatesFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    id_filter: Union[Unset, UUID] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    type_filter: Union[Unset, ERepositoryType] = UNSET,
    capacity_filter: Union[Unset, float] = UNSET,
    free_space_filter: Union[Unset, float] = UNSET,
    used_space_filter: Union[Unset, float] = UNSET,
    is_online_filter: Union[Unset, bool] = UNSET,
    is_out_of_date_filter: Union[Unset, bool] = UNSET,
    sobr_id_filter: Union[Unset, UUID] = UNSET,
    sobr_extent_type_filter: Union[Unset, list[EScaleOutRepositoryExtentType]] = UNSET,
    sobr_membership_filter: Union[Unset, str] = UNSET,
    exclude_extents: Union[Unset, bool] = UNSET,
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

    json_id_filter: Union[Unset, str] = UNSET
    if not isinstance(id_filter, Unset):
        json_id_filter = str(id_filter)
    params["idFilter"] = json_id_filter

    params["nameFilter"] = name_filter

    json_type_filter: Union[Unset, str] = UNSET
    if not isinstance(type_filter, Unset):
        json_type_filter = type_filter.value

    params["typeFilter"] = json_type_filter

    params["capacityFilter"] = capacity_filter

    params["freeSpaceFilter"] = free_space_filter

    params["usedSpaceFilter"] = used_space_filter

    params["isOnlineFilter"] = is_online_filter

    params["isOutOfDateFilter"] = is_out_of_date_filter

    json_sobr_id_filter: Union[Unset, str] = UNSET
    if not isinstance(sobr_id_filter, Unset):
        json_sobr_id_filter = str(sobr_id_filter)
    params["sobrIdFilter"] = json_sobr_id_filter

    json_sobr_extent_type_filter: Union[Unset, list[str]] = UNSET
    if not isinstance(sobr_extent_type_filter, Unset):
        json_sobr_extent_type_filter = []
        for sobr_extent_type_filter_item_data in sobr_extent_type_filter:
            sobr_extent_type_filter_item = sobr_extent_type_filter_item_data.value
            json_sobr_extent_type_filter.append(sobr_extent_type_filter_item)

    params["sobrExtentTypeFilter"] = json_sobr_extent_type_filter

    params["sobrMembershipFilter"] = sobr_membership_filter

    params["excludeExtents"] = exclude_extents

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/backupInfrastructure/repositories/states",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, RepositoryStatesResult]]:
    if response.status_code == 200:
        response_200 = RepositoryStatesResult.from_dict(response.json())

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
) -> Response[Union[Error, RepositoryStatesResult]]:
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
    order_column: Union[Unset, ERepositoryStatesFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    id_filter: Union[Unset, UUID] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    type_filter: Union[Unset, ERepositoryType] = UNSET,
    capacity_filter: Union[Unset, float] = UNSET,
    free_space_filter: Union[Unset, float] = UNSET,
    used_space_filter: Union[Unset, float] = UNSET,
    is_online_filter: Union[Unset, bool] = UNSET,
    is_out_of_date_filter: Union[Unset, bool] = UNSET,
    sobr_id_filter: Union[Unset, UUID] = UNSET,
    sobr_extent_type_filter: Union[Unset, list[EScaleOutRepositoryExtentType]] = UNSET,
    sobr_membership_filter: Union[Unset, str] = UNSET,
    exclude_extents: Union[Unset, bool] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[Union[Error, RepositoryStatesResult]]:
    """Get All Repository States

     The HTTP GET request to the `/api/v1/backupInfrastructure/repositories/states` endpoint gets an
    array of all repository states. The states include repository location and brief statistics, such as
    repository capacity, free and used space.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator.</p>

    Args:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, ERepositoryStatesFiltersOrderColumn]): Orders repositories by
            the specified column.
        order_asc (Union[Unset, bool]):
        id_filter (Union[Unset, UUID]):
        name_filter (Union[Unset, str]):
        type_filter (Union[Unset, ERepositoryType]): Repository type.
        capacity_filter (Union[Unset, float]):
        free_space_filter (Union[Unset, float]):
        used_space_filter (Union[Unset, float]):
        is_online_filter (Union[Unset, bool]):
        is_out_of_date_filter (Union[Unset, bool]):
        sobr_id_filter (Union[Unset, UUID]):
        sobr_extent_type_filter (Union[Unset, list[EScaleOutRepositoryExtentType]]):
        sobr_membership_filter (Union[Unset, str]):
        exclude_extents (Union[Unset, bool]):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, RepositoryStatesResult]]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        id_filter=id_filter,
        name_filter=name_filter,
        type_filter=type_filter,
        capacity_filter=capacity_filter,
        free_space_filter=free_space_filter,
        used_space_filter=used_space_filter,
        is_online_filter=is_online_filter,
        is_out_of_date_filter=is_out_of_date_filter,
        sobr_id_filter=sobr_id_filter,
        sobr_extent_type_filter=sobr_extent_type_filter,
        sobr_membership_filter=sobr_membership_filter,
        exclude_extents=exclude_extents,
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
    order_column: Union[Unset, ERepositoryStatesFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    id_filter: Union[Unset, UUID] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    type_filter: Union[Unset, ERepositoryType] = UNSET,
    capacity_filter: Union[Unset, float] = UNSET,
    free_space_filter: Union[Unset, float] = UNSET,
    used_space_filter: Union[Unset, float] = UNSET,
    is_online_filter: Union[Unset, bool] = UNSET,
    is_out_of_date_filter: Union[Unset, bool] = UNSET,
    sobr_id_filter: Union[Unset, UUID] = UNSET,
    sobr_extent_type_filter: Union[Unset, list[EScaleOutRepositoryExtentType]] = UNSET,
    sobr_membership_filter: Union[Unset, str] = UNSET,
    exclude_extents: Union[Unset, bool] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[Error, RepositoryStatesResult]]:
    """Get All Repository States

     The HTTP GET request to the `/api/v1/backupInfrastructure/repositories/states` endpoint gets an
    array of all repository states. The states include repository location and brief statistics, such as
    repository capacity, free and used space.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator.</p>

    Args:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, ERepositoryStatesFiltersOrderColumn]): Orders repositories by
            the specified column.
        order_asc (Union[Unset, bool]):
        id_filter (Union[Unset, UUID]):
        name_filter (Union[Unset, str]):
        type_filter (Union[Unset, ERepositoryType]): Repository type.
        capacity_filter (Union[Unset, float]):
        free_space_filter (Union[Unset, float]):
        used_space_filter (Union[Unset, float]):
        is_online_filter (Union[Unset, bool]):
        is_out_of_date_filter (Union[Unset, bool]):
        sobr_id_filter (Union[Unset, UUID]):
        sobr_extent_type_filter (Union[Unset, list[EScaleOutRepositoryExtentType]]):
        sobr_membership_filter (Union[Unset, str]):
        exclude_extents (Union[Unset, bool]):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, RepositoryStatesResult]
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        id_filter=id_filter,
        name_filter=name_filter,
        type_filter=type_filter,
        capacity_filter=capacity_filter,
        free_space_filter=free_space_filter,
        used_space_filter=used_space_filter,
        is_online_filter=is_online_filter,
        is_out_of_date_filter=is_out_of_date_filter,
        sobr_id_filter=sobr_id_filter,
        sobr_extent_type_filter=sobr_extent_type_filter,
        sobr_membership_filter=sobr_membership_filter,
        exclude_extents=exclude_extents,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, ERepositoryStatesFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    id_filter: Union[Unset, UUID] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    type_filter: Union[Unset, ERepositoryType] = UNSET,
    capacity_filter: Union[Unset, float] = UNSET,
    free_space_filter: Union[Unset, float] = UNSET,
    used_space_filter: Union[Unset, float] = UNSET,
    is_online_filter: Union[Unset, bool] = UNSET,
    is_out_of_date_filter: Union[Unset, bool] = UNSET,
    sobr_id_filter: Union[Unset, UUID] = UNSET,
    sobr_extent_type_filter: Union[Unset, list[EScaleOutRepositoryExtentType]] = UNSET,
    sobr_membership_filter: Union[Unset, str] = UNSET,
    exclude_extents: Union[Unset, bool] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[Union[Error, RepositoryStatesResult]]:
    """Get All Repository States

     The HTTP GET request to the `/api/v1/backupInfrastructure/repositories/states` endpoint gets an
    array of all repository states. The states include repository location and brief statistics, such as
    repository capacity, free and used space.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator.</p>

    Args:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, ERepositoryStatesFiltersOrderColumn]): Orders repositories by
            the specified column.
        order_asc (Union[Unset, bool]):
        id_filter (Union[Unset, UUID]):
        name_filter (Union[Unset, str]):
        type_filter (Union[Unset, ERepositoryType]): Repository type.
        capacity_filter (Union[Unset, float]):
        free_space_filter (Union[Unset, float]):
        used_space_filter (Union[Unset, float]):
        is_online_filter (Union[Unset, bool]):
        is_out_of_date_filter (Union[Unset, bool]):
        sobr_id_filter (Union[Unset, UUID]):
        sobr_extent_type_filter (Union[Unset, list[EScaleOutRepositoryExtentType]]):
        sobr_membership_filter (Union[Unset, str]):
        exclude_extents (Union[Unset, bool]):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, RepositoryStatesResult]]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        id_filter=id_filter,
        name_filter=name_filter,
        type_filter=type_filter,
        capacity_filter=capacity_filter,
        free_space_filter=free_space_filter,
        used_space_filter=used_space_filter,
        is_online_filter=is_online_filter,
        is_out_of_date_filter=is_out_of_date_filter,
        sobr_id_filter=sobr_id_filter,
        sobr_extent_type_filter=sobr_extent_type_filter,
        sobr_membership_filter=sobr_membership_filter,
        exclude_extents=exclude_extents,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, ERepositoryStatesFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    id_filter: Union[Unset, UUID] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    type_filter: Union[Unset, ERepositoryType] = UNSET,
    capacity_filter: Union[Unset, float] = UNSET,
    free_space_filter: Union[Unset, float] = UNSET,
    used_space_filter: Union[Unset, float] = UNSET,
    is_online_filter: Union[Unset, bool] = UNSET,
    is_out_of_date_filter: Union[Unset, bool] = UNSET,
    sobr_id_filter: Union[Unset, UUID] = UNSET,
    sobr_extent_type_filter: Union[Unset, list[EScaleOutRepositoryExtentType]] = UNSET,
    sobr_membership_filter: Union[Unset, str] = UNSET,
    exclude_extents: Union[Unset, bool] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[Error, RepositoryStatesResult]]:
    """Get All Repository States

     The HTTP GET request to the `/api/v1/backupInfrastructure/repositories/states` endpoint gets an
    array of all repository states. The states include repository location and brief statistics, such as
    repository capacity, free and used space.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator.</p>

    Args:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, ERepositoryStatesFiltersOrderColumn]): Orders repositories by
            the specified column.
        order_asc (Union[Unset, bool]):
        id_filter (Union[Unset, UUID]):
        name_filter (Union[Unset, str]):
        type_filter (Union[Unset, ERepositoryType]): Repository type.
        capacity_filter (Union[Unset, float]):
        free_space_filter (Union[Unset, float]):
        used_space_filter (Union[Unset, float]):
        is_online_filter (Union[Unset, bool]):
        is_out_of_date_filter (Union[Unset, bool]):
        sobr_id_filter (Union[Unset, UUID]):
        sobr_extent_type_filter (Union[Unset, list[EScaleOutRepositoryExtentType]]):
        sobr_membership_filter (Union[Unset, str]):
        exclude_extents (Union[Unset, bool]):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, RepositoryStatesResult]
    """

    return (
        await asyncio_detailed(
            client=client,
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            id_filter=id_filter,
            name_filter=name_filter,
            type_filter=type_filter,
            capacity_filter=capacity_filter,
            free_space_filter=free_space_filter,
            used_space_filter=used_space_filter,
            is_online_filter=is_online_filter,
            is_out_of_date_filter=is_out_of_date_filter,
            sobr_id_filter=sobr_id_filter,
            sobr_extent_type_filter=sobr_extent_type_filter,
            sobr_membership_filter=sobr_membership_filter,
            exclude_extents=exclude_extents,
            x_api_version=x_api_version,
        )
    ).parsed
