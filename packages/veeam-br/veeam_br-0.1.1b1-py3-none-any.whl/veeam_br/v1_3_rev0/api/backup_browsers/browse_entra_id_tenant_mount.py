from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.entra_id_tenant_admin_unit_browse_spec import EntraIdTenantAdminUnitBrowseSpec
from ...models.entra_id_tenant_application_browse_spec import EntraIdTenantApplicationBrowseSpec
from ...models.entra_id_tenant_bitlocker_key_browse_spec import EntraIdTenantBitlockerKeyBrowseSpec
from ...models.entra_id_tenant_browse_result import EntraIdTenantBrowseResult
from ...models.entra_id_tenant_conditional_access_policy_browse_spec import (
    EntraIdTenantConditionalAccessPolicyBrowseSpec,
)
from ...models.entra_id_tenant_device_configuration_browse_spec import EntraIdTenantDeviceConfigurationBrowseSpec
from ...models.entra_id_tenant_group_browse_spec import EntraIdTenantGroupBrowseSpec
from ...models.entra_id_tenant_role_browse_spec import EntraIdTenantRoleBrowseSpec
from ...models.entra_id_tenant_user_browse_spec import EntraIdTenantUserBrowseSpec
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    backup_id: UUID,
    *,
    body: Union[
        "EntraIdTenantAdminUnitBrowseSpec",
        "EntraIdTenantApplicationBrowseSpec",
        "EntraIdTenantBitlockerKeyBrowseSpec",
        "EntraIdTenantConditionalAccessPolicyBrowseSpec",
        "EntraIdTenantDeviceConfigurationBrowseSpec",
        "EntraIdTenantGroupBrowseSpec",
        "EntraIdTenantRoleBrowseSpec",
        "EntraIdTenantUserBrowseSpec",
    ],
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v1/backupBrowser/entraIdTenant/{backup_id}/browse",
    }

    _kwargs["json"]: dict[str, Any]
    if isinstance(body, EntraIdTenantUserBrowseSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, EntraIdTenantGroupBrowseSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, EntraIdTenantAdminUnitBrowseSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, EntraIdTenantRoleBrowseSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, EntraIdTenantApplicationBrowseSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, EntraIdTenantDeviceConfigurationBrowseSpec):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, EntraIdTenantBitlockerKeyBrowseSpec):
        _kwargs["json"] = body.to_dict()
    else:
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[EntraIdTenantBrowseResult, Error]]:
    if response.status_code == 200:
        response_200 = EntraIdTenantBrowseResult.from_dict(response.json())

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

    if response.status_code == 500:
        response_500 = Error.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[EntraIdTenantBrowseResult, Error]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    backup_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        "EntraIdTenantAdminUnitBrowseSpec",
        "EntraIdTenantApplicationBrowseSpec",
        "EntraIdTenantBitlockerKeyBrowseSpec",
        "EntraIdTenantConditionalAccessPolicyBrowseSpec",
        "EntraIdTenantDeviceConfigurationBrowseSpec",
        "EntraIdTenantGroupBrowseSpec",
        "EntraIdTenantRoleBrowseSpec",
        "EntraIdTenantUserBrowseSpec",
    ],
    x_api_version: str = "1.3-rev0",
) -> Response[Union[EntraIdTenantBrowseResult, Error]]:
    """Get Microsoft Entra ID Items

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{backupId}/browse` path allows you
    to browse Microsoft Entra ID items available in a backup that has the specified `backupId`. Use this
    request to find the items that you want to restore. In the request body, you must specify an item
    type&#58; user, group, administrative unit, role or application.<p>**Available to**&#58; Veeam
    Backup Administrator, Veeam Restore Operator.</p>

    Args:
        backup_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.
        body (Union['EntraIdTenantAdminUnitBrowseSpec', 'EntraIdTenantApplicationBrowseSpec',
            'EntraIdTenantBitlockerKeyBrowseSpec', 'EntraIdTenantConditionalAccessPolicyBrowseSpec',
            'EntraIdTenantDeviceConfigurationBrowseSpec', 'EntraIdTenantGroupBrowseSpec',
            'EntraIdTenantRoleBrowseSpec', 'EntraIdTenantUserBrowseSpec']): Settings for Microsoft
            Entra ID tenant.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[EntraIdTenantBrowseResult, Error]]
    """

    kwargs = _get_kwargs(
        backup_id=backup_id,
        body=body,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    backup_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        "EntraIdTenantAdminUnitBrowseSpec",
        "EntraIdTenantApplicationBrowseSpec",
        "EntraIdTenantBitlockerKeyBrowseSpec",
        "EntraIdTenantConditionalAccessPolicyBrowseSpec",
        "EntraIdTenantDeviceConfigurationBrowseSpec",
        "EntraIdTenantGroupBrowseSpec",
        "EntraIdTenantRoleBrowseSpec",
        "EntraIdTenantUserBrowseSpec",
    ],
    x_api_version: str = "1.3-rev0",
) -> Optional[Union[EntraIdTenantBrowseResult, Error]]:
    """Get Microsoft Entra ID Items

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{backupId}/browse` path allows you
    to browse Microsoft Entra ID items available in a backup that has the specified `backupId`. Use this
    request to find the items that you want to restore. In the request body, you must specify an item
    type&#58; user, group, administrative unit, role or application.<p>**Available to**&#58; Veeam
    Backup Administrator, Veeam Restore Operator.</p>

    Args:
        backup_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.
        body (Union['EntraIdTenantAdminUnitBrowseSpec', 'EntraIdTenantApplicationBrowseSpec',
            'EntraIdTenantBitlockerKeyBrowseSpec', 'EntraIdTenantConditionalAccessPolicyBrowseSpec',
            'EntraIdTenantDeviceConfigurationBrowseSpec', 'EntraIdTenantGroupBrowseSpec',
            'EntraIdTenantRoleBrowseSpec', 'EntraIdTenantUserBrowseSpec']): Settings for Microsoft
            Entra ID tenant.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[EntraIdTenantBrowseResult, Error]
    """

    return sync_detailed(
        backup_id=backup_id,
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    backup_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        "EntraIdTenantAdminUnitBrowseSpec",
        "EntraIdTenantApplicationBrowseSpec",
        "EntraIdTenantBitlockerKeyBrowseSpec",
        "EntraIdTenantConditionalAccessPolicyBrowseSpec",
        "EntraIdTenantDeviceConfigurationBrowseSpec",
        "EntraIdTenantGroupBrowseSpec",
        "EntraIdTenantRoleBrowseSpec",
        "EntraIdTenantUserBrowseSpec",
    ],
    x_api_version: str = "1.3-rev0",
) -> Response[Union[EntraIdTenantBrowseResult, Error]]:
    """Get Microsoft Entra ID Items

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{backupId}/browse` path allows you
    to browse Microsoft Entra ID items available in a backup that has the specified `backupId`. Use this
    request to find the items that you want to restore. In the request body, you must specify an item
    type&#58; user, group, administrative unit, role or application.<p>**Available to**&#58; Veeam
    Backup Administrator, Veeam Restore Operator.</p>

    Args:
        backup_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.
        body (Union['EntraIdTenantAdminUnitBrowseSpec', 'EntraIdTenantApplicationBrowseSpec',
            'EntraIdTenantBitlockerKeyBrowseSpec', 'EntraIdTenantConditionalAccessPolicyBrowseSpec',
            'EntraIdTenantDeviceConfigurationBrowseSpec', 'EntraIdTenantGroupBrowseSpec',
            'EntraIdTenantRoleBrowseSpec', 'EntraIdTenantUserBrowseSpec']): Settings for Microsoft
            Entra ID tenant.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[EntraIdTenantBrowseResult, Error]]
    """

    kwargs = _get_kwargs(
        backup_id=backup_id,
        body=body,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    backup_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union[
        "EntraIdTenantAdminUnitBrowseSpec",
        "EntraIdTenantApplicationBrowseSpec",
        "EntraIdTenantBitlockerKeyBrowseSpec",
        "EntraIdTenantConditionalAccessPolicyBrowseSpec",
        "EntraIdTenantDeviceConfigurationBrowseSpec",
        "EntraIdTenantGroupBrowseSpec",
        "EntraIdTenantRoleBrowseSpec",
        "EntraIdTenantUserBrowseSpec",
    ],
    x_api_version: str = "1.3-rev0",
) -> Optional[Union[EntraIdTenantBrowseResult, Error]]:
    """Get Microsoft Entra ID Items

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{backupId}/browse` path allows you
    to browse Microsoft Entra ID items available in a backup that has the specified `backupId`. Use this
    request to find the items that you want to restore. In the request body, you must specify an item
    type&#58; user, group, administrative unit, role or application.<p>**Available to**&#58; Veeam
    Backup Administrator, Veeam Restore Operator.</p>

    Args:
        backup_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.
        body (Union['EntraIdTenantAdminUnitBrowseSpec', 'EntraIdTenantApplicationBrowseSpec',
            'EntraIdTenantBitlockerKeyBrowseSpec', 'EntraIdTenantConditionalAccessPolicyBrowseSpec',
            'EntraIdTenantDeviceConfigurationBrowseSpec', 'EntraIdTenantGroupBrowseSpec',
            'EntraIdTenantRoleBrowseSpec', 'EntraIdTenantUserBrowseSpec']): Settings for Microsoft
            Entra ID tenant.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[EntraIdTenantBrowseResult, Error]
    """

    return (
        await asyncio_detailed(
            backup_id=backup_id,
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed
