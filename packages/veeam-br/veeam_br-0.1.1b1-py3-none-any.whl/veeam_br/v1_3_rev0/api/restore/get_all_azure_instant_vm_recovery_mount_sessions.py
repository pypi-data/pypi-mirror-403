import datetime
from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.e_session_result import ESessionResult
from ...models.e_session_state import ESessionState
from ...models.e_session_type import ESessionType
from ...models.e_sessions_filters_order_column import ESessionsFiltersOrderColumn
from ...models.error import Error
from ...models.sessions_result import SessionsResult
from ...types import UNSET, Response, Unset


def _get_kwargs(
    mount_id: UUID,
    *,
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, ESessionsFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    created_after_filter: Union[Unset, datetime.datetime] = UNSET,
    created_before_filter: Union[Unset, datetime.datetime] = UNSET,
    ended_after_filter: Union[Unset, datetime.datetime] = UNSET,
    ended_before_filter: Union[Unset, datetime.datetime] = UNSET,
    type_filter: Union[Unset, ESessionType] = UNSET,
    state_filter: Union[Unset, ESessionState] = UNSET,
    result_filter: Union[Unset, list[ESessionResult]] = UNSET,
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

    json_created_after_filter: Union[Unset, str] = UNSET
    if not isinstance(created_after_filter, Unset):
        json_created_after_filter = created_after_filter.isoformat()
    params["createdAfterFilter"] = json_created_after_filter

    json_created_before_filter: Union[Unset, str] = UNSET
    if not isinstance(created_before_filter, Unset):
        json_created_before_filter = created_before_filter.isoformat()
    params["createdBeforeFilter"] = json_created_before_filter

    json_ended_after_filter: Union[Unset, str] = UNSET
    if not isinstance(ended_after_filter, Unset):
        json_ended_after_filter = ended_after_filter.isoformat()
    params["endedAfterFilter"] = json_ended_after_filter

    json_ended_before_filter: Union[Unset, str] = UNSET
    if not isinstance(ended_before_filter, Unset):
        json_ended_before_filter = ended_before_filter.isoformat()
    params["endedBeforeFilter"] = json_ended_before_filter

    json_type_filter: Union[Unset, str] = UNSET
    if not isinstance(type_filter, Unset):
        json_type_filter = type_filter.value

    params["typeFilter"] = json_type_filter

    json_state_filter: Union[Unset, str] = UNSET
    if not isinstance(state_filter, Unset):
        json_state_filter = state_filter.value

    params["stateFilter"] = json_state_filter

    json_result_filter: Union[Unset, list[str]] = UNSET
    if not isinstance(result_filter, Unset):
        json_result_filter = []
        for result_filter_item_data in result_filter:
            result_filter_item = result_filter_item_data.value
            json_result_filter.append(result_filter_item)

    params["resultFilter"] = json_result_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/restore/instantRecovery/azure/vm/{mount_id}/sessions",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, SessionsResult]]:
    if response.status_code == 200:
        response_200 = SessionsResult.from_dict(response.json())

        return response_200

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
) -> Response[Union[Error, SessionsResult]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    mount_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, ESessionsFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    created_after_filter: Union[Unset, datetime.datetime] = UNSET,
    created_before_filter: Union[Unset, datetime.datetime] = UNSET,
    ended_after_filter: Union[Unset, datetime.datetime] = UNSET,
    ended_before_filter: Union[Unset, datetime.datetime] = UNSET,
    type_filter: Union[Unset, ESessionType] = UNSET,
    state_filter: Union[Unset, ESessionState] = UNSET,
    result_filter: Union[Unset, list[ESessionResult]] = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[Union[Error, SessionsResult]]:
    """Get All Mount Sessions for Instant Recovery to Azure

     The HTTP GET request to the `/api/v1/restore/instantRecovery/azure/vm/{mountId}/sessions` path
    allows you to get an array of Instant Recovery sessions associated with a mount point.<p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        mount_id (UUID):
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, ESessionsFiltersOrderColumn]):
        order_asc (Union[Unset, bool]):
        created_after_filter (Union[Unset, datetime.datetime]):
        created_before_filter (Union[Unset, datetime.datetime]):
        ended_after_filter (Union[Unset, datetime.datetime]):
        ended_before_filter (Union[Unset, datetime.datetime]):
        type_filter (Union[Unset, ESessionType]): Type of the session.
        state_filter (Union[Unset, ESessionState]): State of the session.
        result_filter (Union[Unset, list[ESessionResult]]):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, SessionsResult]]
    """

    kwargs = _get_kwargs(
        mount_id=mount_id,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        ended_after_filter=ended_after_filter,
        ended_before_filter=ended_before_filter,
        type_filter=type_filter,
        state_filter=state_filter,
        result_filter=result_filter,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    mount_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, ESessionsFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    created_after_filter: Union[Unset, datetime.datetime] = UNSET,
    created_before_filter: Union[Unset, datetime.datetime] = UNSET,
    ended_after_filter: Union[Unset, datetime.datetime] = UNSET,
    ended_before_filter: Union[Unset, datetime.datetime] = UNSET,
    type_filter: Union[Unset, ESessionType] = UNSET,
    state_filter: Union[Unset, ESessionState] = UNSET,
    result_filter: Union[Unset, list[ESessionResult]] = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Optional[Union[Error, SessionsResult]]:
    """Get All Mount Sessions for Instant Recovery to Azure

     The HTTP GET request to the `/api/v1/restore/instantRecovery/azure/vm/{mountId}/sessions` path
    allows you to get an array of Instant Recovery sessions associated with a mount point.<p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        mount_id (UUID):
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, ESessionsFiltersOrderColumn]):
        order_asc (Union[Unset, bool]):
        created_after_filter (Union[Unset, datetime.datetime]):
        created_before_filter (Union[Unset, datetime.datetime]):
        ended_after_filter (Union[Unset, datetime.datetime]):
        ended_before_filter (Union[Unset, datetime.datetime]):
        type_filter (Union[Unset, ESessionType]): Type of the session.
        state_filter (Union[Unset, ESessionState]): State of the session.
        result_filter (Union[Unset, list[ESessionResult]]):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, SessionsResult]
    """

    return sync_detailed(
        mount_id=mount_id,
        client=client,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        ended_after_filter=ended_after_filter,
        ended_before_filter=ended_before_filter,
        type_filter=type_filter,
        state_filter=state_filter,
        result_filter=result_filter,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    mount_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, ESessionsFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    created_after_filter: Union[Unset, datetime.datetime] = UNSET,
    created_before_filter: Union[Unset, datetime.datetime] = UNSET,
    ended_after_filter: Union[Unset, datetime.datetime] = UNSET,
    ended_before_filter: Union[Unset, datetime.datetime] = UNSET,
    type_filter: Union[Unset, ESessionType] = UNSET,
    state_filter: Union[Unset, ESessionState] = UNSET,
    result_filter: Union[Unset, list[ESessionResult]] = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Response[Union[Error, SessionsResult]]:
    """Get All Mount Sessions for Instant Recovery to Azure

     The HTTP GET request to the `/api/v1/restore/instantRecovery/azure/vm/{mountId}/sessions` path
    allows you to get an array of Instant Recovery sessions associated with a mount point.<p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        mount_id (UUID):
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, ESessionsFiltersOrderColumn]):
        order_asc (Union[Unset, bool]):
        created_after_filter (Union[Unset, datetime.datetime]):
        created_before_filter (Union[Unset, datetime.datetime]):
        ended_after_filter (Union[Unset, datetime.datetime]):
        ended_before_filter (Union[Unset, datetime.datetime]):
        type_filter (Union[Unset, ESessionType]): Type of the session.
        state_filter (Union[Unset, ESessionState]): State of the session.
        result_filter (Union[Unset, list[ESessionResult]]):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, SessionsResult]]
    """

    kwargs = _get_kwargs(
        mount_id=mount_id,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        created_after_filter=created_after_filter,
        created_before_filter=created_before_filter,
        ended_after_filter=ended_after_filter,
        ended_before_filter=ended_before_filter,
        type_filter=type_filter,
        state_filter=state_filter,
        result_filter=result_filter,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    mount_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, ESessionsFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    created_after_filter: Union[Unset, datetime.datetime] = UNSET,
    created_before_filter: Union[Unset, datetime.datetime] = UNSET,
    ended_after_filter: Union[Unset, datetime.datetime] = UNSET,
    ended_before_filter: Union[Unset, datetime.datetime] = UNSET,
    type_filter: Union[Unset, ESessionType] = UNSET,
    state_filter: Union[Unset, ESessionState] = UNSET,
    result_filter: Union[Unset, list[ESessionResult]] = UNSET,
    x_api_version: str = "1.3-rev0",
) -> Optional[Union[Error, SessionsResult]]:
    """Get All Mount Sessions for Instant Recovery to Azure

     The HTTP GET request to the `/api/v1/restore/instantRecovery/azure/vm/{mountId}/sessions` path
    allows you to get an array of Instant Recovery sessions associated with a mount point.<p>**Available
    to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        mount_id (UUID):
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, ESessionsFiltersOrderColumn]):
        order_asc (Union[Unset, bool]):
        created_after_filter (Union[Unset, datetime.datetime]):
        created_before_filter (Union[Unset, datetime.datetime]):
        ended_after_filter (Union[Unset, datetime.datetime]):
        ended_before_filter (Union[Unset, datetime.datetime]):
        type_filter (Union[Unset, ESessionType]): Type of the session.
        state_filter (Union[Unset, ESessionState]): State of the session.
        result_filter (Union[Unset, list[ESessionResult]]):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, SessionsResult]
    """

    return (
        await asyncio_detailed(
            mount_id=mount_id,
            client=client,
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            created_after_filter=created_after_filter,
            created_before_filter=created_before_filter,
            ended_after_filter=ended_after_filter,
            ended_before_filter=ended_before_filter,
            type_filter=type_filter,
            state_filter=state_filter,
            result_filter=result_filter,
            x_api_version=x_api_version,
        )
    ).parsed
