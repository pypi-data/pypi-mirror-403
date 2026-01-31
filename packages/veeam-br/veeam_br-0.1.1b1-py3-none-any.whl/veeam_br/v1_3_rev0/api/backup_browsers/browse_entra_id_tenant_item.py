from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.entra_id_tenant_admin_unit_browse_model import EntraIdTenantAdminUnitBrowseModel
from ...models.entra_id_tenant_application_browse_model import EntraIdTenantApplicationBrowseModel
from ...models.entra_id_tenant_bitlocker_key_browse_model import EntraIdTenantBitlockerKeyBrowseModel
from ...models.entra_id_tenant_conditional_access_policy_browse_model import (
    EntraIdTenantConditionalAccessPolicyBrowseModel,
)
from ...models.entra_id_tenant_device_configuration_browse_model import EntraIdTenantDeviceConfigurationBrowseModel
from ...models.entra_id_tenant_group_browse_model import EntraIdTenantGroupBrowseModel
from ...models.entra_id_tenant_item_type_spec import EntraIdTenantItemTypeSpec
from ...models.entra_id_tenant_role_browse_model import EntraIdTenantRoleBrowseModel
from ...models.entra_id_tenant_user_browse_model import EntraIdTenantUserBrowseModel
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    backup_id: UUID,
    item_id: str,
    *,
    body: EntraIdTenantItemTypeSpec,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v1/backupBrowser/entraIdTenant/{backup_id}/browse/{item_id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        Error,
        Union[
            "EntraIdTenantAdminUnitBrowseModel",
            "EntraIdTenantApplicationBrowseModel",
            "EntraIdTenantBitlockerKeyBrowseModel",
            "EntraIdTenantConditionalAccessPolicyBrowseModel",
            "EntraIdTenantDeviceConfigurationBrowseModel",
            "EntraIdTenantGroupBrowseModel",
            "EntraIdTenantRoleBrowseModel",
            "EntraIdTenantUserBrowseModel",
        ],
    ]
]:
    if response.status_code == 200:

        def _parse_response_200(
            data: object,
        ) -> Union[
            "EntraIdTenantAdminUnitBrowseModel",
            "EntraIdTenantApplicationBrowseModel",
            "EntraIdTenantBitlockerKeyBrowseModel",
            "EntraIdTenantConditionalAccessPolicyBrowseModel",
            "EntraIdTenantDeviceConfigurationBrowseModel",
            "EntraIdTenantGroupBrowseModel",
            "EntraIdTenantRoleBrowseModel",
            "EntraIdTenantUserBrowseModel",
        ]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_entra_id_tenant_browse_model_type_0 = EntraIdTenantUserBrowseModel.from_dict(data)

                return componentsschemas_entra_id_tenant_browse_model_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_entra_id_tenant_browse_model_type_1 = EntraIdTenantGroupBrowseModel.from_dict(data)

                return componentsschemas_entra_id_tenant_browse_model_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_entra_id_tenant_browse_model_type_2 = EntraIdTenantAdminUnitBrowseModel.from_dict(
                    data
                )

                return componentsschemas_entra_id_tenant_browse_model_type_2
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_entra_id_tenant_browse_model_type_3 = EntraIdTenantRoleBrowseModel.from_dict(data)

                return componentsschemas_entra_id_tenant_browse_model_type_3
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_entra_id_tenant_browse_model_type_4 = EntraIdTenantApplicationBrowseModel.from_dict(
                    data
                )

                return componentsschemas_entra_id_tenant_browse_model_type_4
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_entra_id_tenant_browse_model_type_5 = (
                    EntraIdTenantDeviceConfigurationBrowseModel.from_dict(data)
                )

                return componentsschemas_entra_id_tenant_browse_model_type_5
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_entra_id_tenant_browse_model_type_6 = EntraIdTenantBitlockerKeyBrowseModel.from_dict(
                    data
                )

                return componentsschemas_entra_id_tenant_browse_model_type_6
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_entra_id_tenant_browse_model_type_7 = (
                EntraIdTenantConditionalAccessPolicyBrowseModel.from_dict(data)
            )

            return componentsschemas_entra_id_tenant_browse_model_type_7

        response_200 = _parse_response_200(response.json())

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
) -> Response[
    Union[
        Error,
        Union[
            "EntraIdTenantAdminUnitBrowseModel",
            "EntraIdTenantApplicationBrowseModel",
            "EntraIdTenantBitlockerKeyBrowseModel",
            "EntraIdTenantConditionalAccessPolicyBrowseModel",
            "EntraIdTenantDeviceConfigurationBrowseModel",
            "EntraIdTenantGroupBrowseModel",
            "EntraIdTenantRoleBrowseModel",
            "EntraIdTenantUserBrowseModel",
        ],
    ]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    backup_id: UUID,
    item_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: EntraIdTenantItemTypeSpec,
    x_api_version: str = "1.3-rev0",
) -> Response[
    Union[
        Error,
        Union[
            "EntraIdTenantAdminUnitBrowseModel",
            "EntraIdTenantApplicationBrowseModel",
            "EntraIdTenantBitlockerKeyBrowseModel",
            "EntraIdTenantConditionalAccessPolicyBrowseModel",
            "EntraIdTenantDeviceConfigurationBrowseModel",
            "EntraIdTenantGroupBrowseModel",
            "EntraIdTenantRoleBrowseModel",
            "EntraIdTenantUserBrowseModel",
        ],
    ]
]:
    """Get Microsoft Entra ID Item

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{backupId}/browse/{itemId}` path
    allows you to get a specific Microsoft Entra ID item available in a tenant backup that has the
    specified `backupId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore
    Operator.</p>

    Args:
        backup_id (UUID):
        item_id (str):
        x_api_version (str):  Default: '1.3-rev0'.
        body (EntraIdTenantItemTypeSpec): Item type settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['EntraIdTenantAdminUnitBrowseModel', 'EntraIdTenantApplicationBrowseModel', 'EntraIdTenantBitlockerKeyBrowseModel', 'EntraIdTenantConditionalAccessPolicyBrowseModel', 'EntraIdTenantDeviceConfigurationBrowseModel', 'EntraIdTenantGroupBrowseModel', 'EntraIdTenantRoleBrowseModel', 'EntraIdTenantUserBrowseModel']]]
    """

    kwargs = _get_kwargs(
        backup_id=backup_id,
        item_id=item_id,
        body=body,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    backup_id: UUID,
    item_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: EntraIdTenantItemTypeSpec,
    x_api_version: str = "1.3-rev0",
) -> Optional[
    Union[
        Error,
        Union[
            "EntraIdTenantAdminUnitBrowseModel",
            "EntraIdTenantApplicationBrowseModel",
            "EntraIdTenantBitlockerKeyBrowseModel",
            "EntraIdTenantConditionalAccessPolicyBrowseModel",
            "EntraIdTenantDeviceConfigurationBrowseModel",
            "EntraIdTenantGroupBrowseModel",
            "EntraIdTenantRoleBrowseModel",
            "EntraIdTenantUserBrowseModel",
        ],
    ]
]:
    """Get Microsoft Entra ID Item

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{backupId}/browse/{itemId}` path
    allows you to get a specific Microsoft Entra ID item available in a tenant backup that has the
    specified `backupId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore
    Operator.</p>

    Args:
        backup_id (UUID):
        item_id (str):
        x_api_version (str):  Default: '1.3-rev0'.
        body (EntraIdTenantItemTypeSpec): Item type settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['EntraIdTenantAdminUnitBrowseModel', 'EntraIdTenantApplicationBrowseModel', 'EntraIdTenantBitlockerKeyBrowseModel', 'EntraIdTenantConditionalAccessPolicyBrowseModel', 'EntraIdTenantDeviceConfigurationBrowseModel', 'EntraIdTenantGroupBrowseModel', 'EntraIdTenantRoleBrowseModel', 'EntraIdTenantUserBrowseModel']]
    """

    return sync_detailed(
        backup_id=backup_id,
        item_id=item_id,
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    backup_id: UUID,
    item_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: EntraIdTenantItemTypeSpec,
    x_api_version: str = "1.3-rev0",
) -> Response[
    Union[
        Error,
        Union[
            "EntraIdTenantAdminUnitBrowseModel",
            "EntraIdTenantApplicationBrowseModel",
            "EntraIdTenantBitlockerKeyBrowseModel",
            "EntraIdTenantConditionalAccessPolicyBrowseModel",
            "EntraIdTenantDeviceConfigurationBrowseModel",
            "EntraIdTenantGroupBrowseModel",
            "EntraIdTenantRoleBrowseModel",
            "EntraIdTenantUserBrowseModel",
        ],
    ]
]:
    """Get Microsoft Entra ID Item

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{backupId}/browse/{itemId}` path
    allows you to get a specific Microsoft Entra ID item available in a tenant backup that has the
    specified `backupId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore
    Operator.</p>

    Args:
        backup_id (UUID):
        item_id (str):
        x_api_version (str):  Default: '1.3-rev0'.
        body (EntraIdTenantItemTypeSpec): Item type settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['EntraIdTenantAdminUnitBrowseModel', 'EntraIdTenantApplicationBrowseModel', 'EntraIdTenantBitlockerKeyBrowseModel', 'EntraIdTenantConditionalAccessPolicyBrowseModel', 'EntraIdTenantDeviceConfigurationBrowseModel', 'EntraIdTenantGroupBrowseModel', 'EntraIdTenantRoleBrowseModel', 'EntraIdTenantUserBrowseModel']]]
    """

    kwargs = _get_kwargs(
        backup_id=backup_id,
        item_id=item_id,
        body=body,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    backup_id: UUID,
    item_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: EntraIdTenantItemTypeSpec,
    x_api_version: str = "1.3-rev0",
) -> Optional[
    Union[
        Error,
        Union[
            "EntraIdTenantAdminUnitBrowseModel",
            "EntraIdTenantApplicationBrowseModel",
            "EntraIdTenantBitlockerKeyBrowseModel",
            "EntraIdTenantConditionalAccessPolicyBrowseModel",
            "EntraIdTenantDeviceConfigurationBrowseModel",
            "EntraIdTenantGroupBrowseModel",
            "EntraIdTenantRoleBrowseModel",
            "EntraIdTenantUserBrowseModel",
        ],
    ]
]:
    """Get Microsoft Entra ID Item

     The HTTP POST request to the `/api/v1/backupBrowser/entraIdTenant/{backupId}/browse/{itemId}` path
    allows you to get a specific Microsoft Entra ID item available in a tenant backup that has the
    specified `backupId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore
    Operator.</p>

    Args:
        backup_id (UUID):
        item_id (str):
        x_api_version (str):  Default: '1.3-rev0'.
        body (EntraIdTenantItemTypeSpec): Item type settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['EntraIdTenantAdminUnitBrowseModel', 'EntraIdTenantApplicationBrowseModel', 'EntraIdTenantBitlockerKeyBrowseModel', 'EntraIdTenantConditionalAccessPolicyBrowseModel', 'EntraIdTenantDeviceConfigurationBrowseModel', 'EntraIdTenantGroupBrowseModel', 'EntraIdTenantRoleBrowseModel', 'EntraIdTenantUserBrowseModel']]
    """

    return (
        await asyncio_detailed(
            backup_id=backup_id,
            item_id=item_id,
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed
