from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.inventory_browser_filters import InventoryBrowserFilters
from ...types import Response


def _get_kwargs(
    protection_group_id: UUID,
    *,
    body: InventoryBrowserFilters,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v1/inventory/physical/{protection_group_id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

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
    protection_group_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: InventoryBrowserFilters,
    x_api_version: str = "1.3-rev0",
) -> Response[Error]:
    """Get Inventory Objects for Specific Protection Group

     The HTTP POST request to the `/api/v1/inventory/physical/{protectionGroupId}` path allows you to get
    an array of inventory objects of physical or cloud machines for a protection group with the
    specified `protectionGroupId`. <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        protection_group_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.
        body (InventoryBrowserFilters):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error]
    """

    kwargs = _get_kwargs(
        protection_group_id=protection_group_id,
        body=body,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    protection_group_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: InventoryBrowserFilters,
    x_api_version: str = "1.3-rev0",
) -> Optional[Error]:
    """Get Inventory Objects for Specific Protection Group

     The HTTP POST request to the `/api/v1/inventory/physical/{protectionGroupId}` path allows you to get
    an array of inventory objects of physical or cloud machines for a protection group with the
    specified `protectionGroupId`. <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        protection_group_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.
        body (InventoryBrowserFilters):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error
    """

    return sync_detailed(
        protection_group_id=protection_group_id,
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    protection_group_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: InventoryBrowserFilters,
    x_api_version: str = "1.3-rev0",
) -> Response[Error]:
    """Get Inventory Objects for Specific Protection Group

     The HTTP POST request to the `/api/v1/inventory/physical/{protectionGroupId}` path allows you to get
    an array of inventory objects of physical or cloud machines for a protection group with the
    specified `protectionGroupId`. <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        protection_group_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.
        body (InventoryBrowserFilters):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error]
    """

    kwargs = _get_kwargs(
        protection_group_id=protection_group_id,
        body=body,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    protection_group_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: InventoryBrowserFilters,
    x_api_version: str = "1.3-rev0",
) -> Optional[Error]:
    """Get Inventory Objects for Specific Protection Group

     The HTTP POST request to the `/api/v1/inventory/physical/{protectionGroupId}` path allows you to get
    an array of inventory objects of physical or cloud machines for a protection group with the
    specified `protectionGroupId`. <p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        protection_group_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.
        body (InventoryBrowserFilters):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error
    """

    return (
        await asyncio_detailed(
            protection_group_id=protection_group_id,
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed
