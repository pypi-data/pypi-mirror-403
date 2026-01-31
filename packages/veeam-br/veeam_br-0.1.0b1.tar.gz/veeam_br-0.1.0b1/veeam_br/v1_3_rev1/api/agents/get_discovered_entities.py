from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.e_discovered_entity_filters_order_column import EDiscoveredEntityFiltersOrderColumn
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: UUID,
    *,
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, EDiscoveredEntityFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    ip_address_filter: Union[Unset, str] = UNSET,
    state_filter: Union[Unset, str] = UNSET,
    agent_status_filter: Union[Unset, str] = UNSET,
    driver_status_filter: Union[Unset, str] = UNSET,
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

    params["ipAddressFilter"] = ip_address_filter

    params["stateFilter"] = state_filter

    params["agentStatusFilter"] = agent_status_filter

    params["driverStatusFilter"] = driver_status_filter

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/agents/protectionGroups/{id}/discoveredEntities",
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


def _build_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Response[Error]:
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
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, EDiscoveredEntityFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    ip_address_filter: Union[Unset, str] = UNSET,
    state_filter: Union[Unset, str] = UNSET,
    agent_status_filter: Union[Unset, str] = UNSET,
    driver_status_filter: Union[Unset, str] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[Error]:
    """Get Discovered Entities

     The HTTP GET request to the `/api/v1/agents/protectionGroups/{id}/discoveredEntities` endpoint gets
    a list of discovered entities — a list of individual computers, clusters or Active Directory objects
    processed in the scope of the protection group that has the specified `id`. <p>**Available to**&#58;
    Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, EDiscoveredEntityFiltersOrderColumn]): Sorts discovered
            entities by one of the parameters.
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        ip_address_filter (Union[Unset, str]):
        state_filter (Union[Unset, str]):
        agent_status_filter (Union[Unset, str]):
        driver_status_filter (Union[Unset, str]):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error]
    """

    kwargs = _get_kwargs(
        id=id,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        ip_address_filter=ip_address_filter,
        state_filter=state_filter,
        agent_status_filter=agent_status_filter,
        driver_status_filter=driver_status_filter,
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
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, EDiscoveredEntityFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    ip_address_filter: Union[Unset, str] = UNSET,
    state_filter: Union[Unset, str] = UNSET,
    agent_status_filter: Union[Unset, str] = UNSET,
    driver_status_filter: Union[Unset, str] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Optional[Error]:
    """Get Discovered Entities

     The HTTP GET request to the `/api/v1/agents/protectionGroups/{id}/discoveredEntities` endpoint gets
    a list of discovered entities — a list of individual computers, clusters or Active Directory objects
    processed in the scope of the protection group that has the specified `id`. <p>**Available to**&#58;
    Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, EDiscoveredEntityFiltersOrderColumn]): Sorts discovered
            entities by one of the parameters.
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        ip_address_filter (Union[Unset, str]):
        state_filter (Union[Unset, str]):
        agent_status_filter (Union[Unset, str]):
        driver_status_filter (Union[Unset, str]):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error
    """

    return sync_detailed(
        id=id,
        client=client,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        ip_address_filter=ip_address_filter,
        state_filter=state_filter,
        agent_status_filter=agent_status_filter,
        driver_status_filter=driver_status_filter,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, EDiscoveredEntityFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    ip_address_filter: Union[Unset, str] = UNSET,
    state_filter: Union[Unset, str] = UNSET,
    agent_status_filter: Union[Unset, str] = UNSET,
    driver_status_filter: Union[Unset, str] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[Error]:
    """Get Discovered Entities

     The HTTP GET request to the `/api/v1/agents/protectionGroups/{id}/discoveredEntities` endpoint gets
    a list of discovered entities — a list of individual computers, clusters or Active Directory objects
    processed in the scope of the protection group that has the specified `id`. <p>**Available to**&#58;
    Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, EDiscoveredEntityFiltersOrderColumn]): Sorts discovered
            entities by one of the parameters.
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        ip_address_filter (Union[Unset, str]):
        state_filter (Union[Unset, str]):
        agent_status_filter (Union[Unset, str]):
        driver_status_filter (Union[Unset, str]):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error]
    """

    kwargs = _get_kwargs(
        id=id,
        skip=skip,
        limit=limit,
        order_column=order_column,
        order_asc=order_asc,
        name_filter=name_filter,
        ip_address_filter=ip_address_filter,
        state_filter=state_filter,
        agent_status_filter=agent_status_filter,
        driver_status_filter=driver_status_filter,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = UNSET,
    limit: Union[Unset, int] = 200,
    order_column: Union[Unset, EDiscoveredEntityFiltersOrderColumn] = UNSET,
    order_asc: Union[Unset, bool] = UNSET,
    name_filter: Union[Unset, str] = UNSET,
    ip_address_filter: Union[Unset, str] = UNSET,
    state_filter: Union[Unset, str] = UNSET,
    agent_status_filter: Union[Unset, str] = UNSET,
    driver_status_filter: Union[Unset, str] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Optional[Error]:
    """Get Discovered Entities

     The HTTP GET request to the `/api/v1/agents/protectionGroups/{id}/discoveredEntities` endpoint gets
    a list of discovered entities — a list of individual computers, clusters or Active Directory objects
    processed in the scope of the protection group that has the specified `id`. <p>**Available to**&#58;
    Veeam Backup Administrator.</p>

    Args:
        id (UUID):
        skip (Union[Unset, int]):
        limit (Union[Unset, int]):  Default: 200.
        order_column (Union[Unset, EDiscoveredEntityFiltersOrderColumn]): Sorts discovered
            entities by one of the parameters.
        order_asc (Union[Unset, bool]):
        name_filter (Union[Unset, str]):
        ip_address_filter (Union[Unset, str]):
        state_filter (Union[Unset, str]):
        agent_status_filter (Union[Unset, str]):
        driver_status_filter (Union[Unset, str]):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            skip=skip,
            limit=limit,
            order_column=order_column,
            order_asc=order_asc,
            name_filter=name_filter,
            ip_address_filter=ip_address_filter,
            state_filter=state_filter,
            agent_status_filter=agent_status_filter,
            driver_status_filter=driver_status_filter,
            x_api_version=x_api_version,
        )
    ).parsed
