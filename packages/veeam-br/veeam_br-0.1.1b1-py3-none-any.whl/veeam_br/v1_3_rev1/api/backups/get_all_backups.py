import datetime
from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.backups_result import BackupsResult
from ...models.e_backups_filters_order_column import EBackupsFiltersOrderColumn
from ...models.e_job_type import EJobType
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, EBackupsFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    created_after_filter: Union[Unset, datetime.datetime] = UNSET,
    created_before_filter: Union[Unset, datetime.datetime] = UNSET,
    platform_id_filter: Union[Unset, UUID] = UNSET,
    job_id_filter: Union[Unset, UUID] = UNSET,
    policy_tag_filter: Union[Unset, str] = UNSET,
    job_type_filter: Union[Unset, EJobType] = UNSET,
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

    json_created_after_filter: Union[Unset, str] = UNSET
    if not isinstance(created_after_filter, Unset):
        json_created_after_filter = created_after_filter.isoformat()
    params["createdAfterFilter"] = json_created_after_filter

    json_created_before_filter: Union[Unset, str] = UNSET
    if not isinstance(created_before_filter, Unset):
        json_created_before_filter = created_before_filter.isoformat()
    params["createdBeforeFilter"] = json_created_before_filter

    json_platform_id_filter: Union[Unset, str] = UNSET
    if not isinstance(platform_id_filter, Unset):
        json_platform_id_filter = str(platform_id_filter)
    params["platformIdFilter"] = json_platform_id_filter

    json_job_id_filter: Union[Unset, str] = UNSET
    if not isinstance(job_id_filter, Unset):
        json_job_id_filter = str(job_id_filter)
    params["jobIdFilter"] = json_job_id_filter

    params["policyTagFilter"] = policy_tag_filter

    json_job_type_filter: Union[Unset, str] = UNSET
    if not isinstance(job_type_filter, Unset):
        json_job_type_filter = job_type_filter.value

    params["jobTypeFilter"] = json_job_type_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/backups",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[BackupsResult, Error]]:
    if response.status_code == 200:
        response_200 = BackupsResult.from_dict(response.json())

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
) -> Response[Union[BackupsResult, Error]]:
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
    order_column: Union[Unset, EBackupsFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    created_after_filter: Union[Unset, datetime.datetime] = UNSET,
    created_before_filter: Union[Unset, datetime.datetime] = UNSET,
    platform_id_filter: Union[Unset, UUID] = UNSET,
    job_id_filter: Union[Unset, UUID] = UNSET,
    policy_tag_filter: Union[Unset, str] = UNSET,
    job_type_filter: Union[Unset, EJobType] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[Union[BackupsResult, Error]]:
    """Get All Backups

     The HTTP GET request to the `/api/v1/backups` endpoint gets an array of all backups that are created
    on or imported to the backup server.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator, Veeam Security
    Administrator.</p>

    Args:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, EBackupsFiltersOrderColumn]):
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        created_after_filter (Union[Unset, datetime.datetime]):
        created_before_filter (Union[Unset, datetime.datetime]):
        platform_id_filter (Union[Unset, UUID]):
        job_id_filter (Union[Unset, UUID]):
        policy_tag_filter (Union[Unset, str]):
        job_type_filter (Union[Unset, EJobType]): Type of the job.
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[BackupsResult, Error]]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        platform_id_filter=platform_id_filter,
        job_id_filter=job_id_filter,
        policy_tag_filter=policy_tag_filter,
        job_type_filter=job_type_filter,
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
    order_column: Union[Unset, EBackupsFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    created_after_filter: Union[Unset, datetime.datetime] = UNSET,
    created_before_filter: Union[Unset, datetime.datetime] = UNSET,
    platform_id_filter: Union[Unset, UUID] = UNSET,
    job_id_filter: Union[Unset, UUID] = UNSET,
    policy_tag_filter: Union[Unset, str] = UNSET,
    job_type_filter: Union[Unset, EJobType] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[BackupsResult, Error]]:
    """Get All Backups

     The HTTP GET request to the `/api/v1/backups` endpoint gets an array of all backups that are created
    on or imported to the backup server.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator, Veeam Security
    Administrator.</p>

    Args:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, EBackupsFiltersOrderColumn]):
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        created_after_filter (Union[Unset, datetime.datetime]):
        created_before_filter (Union[Unset, datetime.datetime]):
        platform_id_filter (Union[Unset, UUID]):
        job_id_filter (Union[Unset, UUID]):
        policy_tag_filter (Union[Unset, str]):
        job_type_filter (Union[Unset, EJobType]): Type of the job.
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[BackupsResult, Error]
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        platform_id_filter=platform_id_filter,
        job_id_filter=job_id_filter,
        policy_tag_filter=policy_tag_filter,
        job_type_filter=job_type_filter,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, EBackupsFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    created_after_filter: Union[Unset, datetime.datetime] = UNSET,
    created_before_filter: Union[Unset, datetime.datetime] = UNSET,
    platform_id_filter: Union[Unset, UUID] = UNSET,
    job_id_filter: Union[Unset, UUID] = UNSET,
    policy_tag_filter: Union[Unset, str] = UNSET,
    job_type_filter: Union[Unset, EJobType] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[Union[BackupsResult, Error]]:
    """Get All Backups

     The HTTP GET request to the `/api/v1/backups` endpoint gets an array of all backups that are created
    on or imported to the backup server.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator, Veeam Security
    Administrator.</p>

    Args:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, EBackupsFiltersOrderColumn]):
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        created_after_filter (Union[Unset, datetime.datetime]):
        created_before_filter (Union[Unset, datetime.datetime]):
        platform_id_filter (Union[Unset, UUID]):
        job_id_filter (Union[Unset, UUID]):
        policy_tag_filter (Union[Unset, str]):
        job_type_filter (Union[Unset, EJobType]): Type of the job.
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[BackupsResult, Error]]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        platform_id_filter=platform_id_filter,
        job_id_filter=job_id_filter,
        policy_tag_filter=policy_tag_filter,
        job_type_filter=job_type_filter,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, EBackupsFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    created_after_filter: Union[Unset, datetime.datetime] = UNSET,
    created_before_filter: Union[Unset, datetime.datetime] = UNSET,
    platform_id_filter: Union[Unset, UUID] = UNSET,
    job_id_filter: Union[Unset, UUID] = UNSET,
    policy_tag_filter: Union[Unset, str] = UNSET,
    job_type_filter: Union[Unset, EJobType] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[BackupsResult, Error]]:
    """Get All Backups

     The HTTP GET request to the `/api/v1/backups` endpoint gets an array of all backups that are created
    on or imported to the backup server.<p>**Available to**&#58; Veeam Backup Administrator, Veeam
    Backup Operator, Veeam Restore Operator, Veeam Backup Viewer, Veeam Tape Operator, Veeam Security
    Administrator.</p>

    Args:
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, EBackupsFiltersOrderColumn]):
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        created_after_filter (Union[Unset, datetime.datetime]):
        created_before_filter (Union[Unset, datetime.datetime]):
        platform_id_filter (Union[Unset, UUID]):
        job_id_filter (Union[Unset, UUID]):
        policy_tag_filter (Union[Unset, str]):
        job_type_filter (Union[Unset, EJobType]): Type of the job.
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[BackupsResult, Error]
    """

    return (
        await asyncio_detailed(
            client=client,
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            created_after_filter=created_after_filter,
            created_before_filter=created_before_filter,
            platform_id_filter=platform_id_filter,
            job_id_filter=job_id_filter,
            policy_tag_filter=policy_tag_filter,
            job_type_filter=job_type_filter,
            x_api_version=x_api_version,
        )
    ).parsed
