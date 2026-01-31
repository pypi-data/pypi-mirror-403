from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.azure_instant_vm_recovery_switchover_settings_model import AzureInstantVMRecoverySwitchoverSettingsModel
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    mount_id: UUID,
    *,
    body: AzureInstantVMRecoverySwitchoverSettingsModel,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/api/v1/restore/instantRecovery/azure/vm/{mount_id}/switchoverSettings",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[AzureInstantVMRecoverySwitchoverSettingsModel, Error]]:
    if response.status_code == 201:
        response_201 = AzureInstantVMRecoverySwitchoverSettingsModel.from_dict(response.json())

        return response_201

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
) -> Response[Union[AzureInstantVMRecoverySwitchoverSettingsModel, Error]]:
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
    body: AzureInstantVMRecoverySwitchoverSettingsModel,
    x_api_version: str = "1.3-rev1",
) -> Response[Union[AzureInstantVMRecoverySwitchoverSettingsModel, Error]]:
    """Update Settings for Switchover to Microsoft Azure

     The HTTP PUT request to the `/api/v1/restore/instantRecovery/azure/vm/{mountId}/switchoverSettings`
    endpoint modifies switchover settings for an Instant Recovery mount point that has the specified
    `mountID`.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (AzureInstantVMRecoverySwitchoverSettingsModel): Switchover settings for Instant
            Recovery to Microsoft Azure.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AzureInstantVMRecoverySwitchoverSettingsModel, Error]]
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
    body: AzureInstantVMRecoverySwitchoverSettingsModel,
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[AzureInstantVMRecoverySwitchoverSettingsModel, Error]]:
    """Update Settings for Switchover to Microsoft Azure

     The HTTP PUT request to the `/api/v1/restore/instantRecovery/azure/vm/{mountId}/switchoverSettings`
    endpoint modifies switchover settings for an Instant Recovery mount point that has the specified
    `mountID`.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (AzureInstantVMRecoverySwitchoverSettingsModel): Switchover settings for Instant
            Recovery to Microsoft Azure.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AzureInstantVMRecoverySwitchoverSettingsModel, Error]
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
    body: AzureInstantVMRecoverySwitchoverSettingsModel,
    x_api_version: str = "1.3-rev1",
) -> Response[Union[AzureInstantVMRecoverySwitchoverSettingsModel, Error]]:
    """Update Settings for Switchover to Microsoft Azure

     The HTTP PUT request to the `/api/v1/restore/instantRecovery/azure/vm/{mountId}/switchoverSettings`
    endpoint modifies switchover settings for an Instant Recovery mount point that has the specified
    `mountID`.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (AzureInstantVMRecoverySwitchoverSettingsModel): Switchover settings for Instant
            Recovery to Microsoft Azure.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AzureInstantVMRecoverySwitchoverSettingsModel, Error]]
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
    body: AzureInstantVMRecoverySwitchoverSettingsModel,
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[AzureInstantVMRecoverySwitchoverSettingsModel, Error]]:
    """Update Settings for Switchover to Microsoft Azure

     The HTTP PUT request to the `/api/v1/restore/instantRecovery/azure/vm/{mountId}/switchoverSettings`
    endpoint modifies switchover settings for an Instant Recovery mount point that has the specified
    `mountID`.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        mount_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.
        body (AzureInstantVMRecoverySwitchoverSettingsModel): Switchover settings for Instant
            Recovery to Microsoft Azure.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AzureInstantVMRecoverySwitchoverSettingsModel, Error]
    """

    return (
        await asyncio_detailed(
            mount_id=mount_id,
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed
