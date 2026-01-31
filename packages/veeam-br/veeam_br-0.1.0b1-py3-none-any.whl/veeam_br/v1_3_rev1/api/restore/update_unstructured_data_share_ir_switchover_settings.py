from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.unstructured_data_switchover_settings_model import UnstructuredDataSwitchoverSettingsModel
from ...types import Response


def _get_kwargs(
    mount_id: UUID,
    *,
    body: UnstructuredDataSwitchoverSettingsModel,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/api/v1/restore/instantRecovery/unstructuredData/{mount_id}/switchoverSettings",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, UnstructuredDataSwitchoverSettingsModel]]:
    if response.status_code == 200:
        response_200 = UnstructuredDataSwitchoverSettingsModel.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400

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
) -> Response[Union[Error, UnstructuredDataSwitchoverSettingsModel]]:
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
    body: UnstructuredDataSwitchoverSettingsModel,
    x_api_version: str = "1.3-rev1",
) -> Response[Union[Error, UnstructuredDataSwitchoverSettingsModel]]:
    """Update File Share Switchover Settings

     The HTTP PUT request to the
    `/api/v1/restore/instantRecovery/unstructuredData/{mountId}/switchoverSettings` endpoint modifies
    switchover settings for an Instant Recovery mount point that has the specified
    `mountID`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (UnstructuredDataSwitchoverSettingsModel): Switchover settings for Instant File Share
            Recovery.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, UnstructuredDataSwitchoverSettingsModel]]
    """

    kwargs = _get_kwargs(
        mount_id=mount_id,
        body=body,
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
    body: UnstructuredDataSwitchoverSettingsModel,
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[Error, UnstructuredDataSwitchoverSettingsModel]]:
    """Update File Share Switchover Settings

     The HTTP PUT request to the
    `/api/v1/restore/instantRecovery/unstructuredData/{mountId}/switchoverSettings` endpoint modifies
    switchover settings for an Instant Recovery mount point that has the specified
    `mountID`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (UnstructuredDataSwitchoverSettingsModel): Switchover settings for Instant File Share
            Recovery.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, UnstructuredDataSwitchoverSettingsModel]
    """

    return sync_detailed(
        mount_id=mount_id,
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    mount_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UnstructuredDataSwitchoverSettingsModel,
    x_api_version: str = "1.3-rev1",
) -> Response[Union[Error, UnstructuredDataSwitchoverSettingsModel]]:
    """Update File Share Switchover Settings

     The HTTP PUT request to the
    `/api/v1/restore/instantRecovery/unstructuredData/{mountId}/switchoverSettings` endpoint modifies
    switchover settings for an Instant Recovery mount point that has the specified
    `mountID`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (UnstructuredDataSwitchoverSettingsModel): Switchover settings for Instant File Share
            Recovery.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, UnstructuredDataSwitchoverSettingsModel]]
    """

    kwargs = _get_kwargs(
        mount_id=mount_id,
        body=body,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    mount_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UnstructuredDataSwitchoverSettingsModel,
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[Error, UnstructuredDataSwitchoverSettingsModel]]:
    """Update File Share Switchover Settings

     The HTTP PUT request to the
    `/api/v1/restore/instantRecovery/unstructuredData/{mountId}/switchoverSettings` endpoint modifies
    switchover settings for an Instant Recovery mount point that has the specified
    `mountID`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (UnstructuredDataSwitchoverSettingsModel): Switchover settings for Instant File Share
            Recovery.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, UnstructuredDataSwitchoverSettingsModel]
    """

    return (
        await asyncio_detailed(
            mount_id=mount_id,
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed
