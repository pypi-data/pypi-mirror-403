from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.entra_id_tenant_item_comparison_session_model import EntraIdTenantItemComparisonSessionModel
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    session_id: UUID,
    compare_session_id: UUID,
    *,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/backupBrowser/entraIdTenant/{session_id}/compare/{compare_session_id}/result",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[EntraIdTenantItemComparisonSessionModel, Error]]:
    if response.status_code == 200:
        response_200 = EntraIdTenantItemComparisonSessionModel.from_dict(response.json())

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
) -> Response[Union[EntraIdTenantItemComparisonSessionModel, Error]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    session_id: UUID,
    compare_session_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev0",
) -> Response[Union[EntraIdTenantItemComparisonSessionModel, Error]]:
    """Get Comparison Results for Microsoft Entra ID Items

     The HTTP GET request to the
    `/api/v1/backupBrowser/entraIdTenant/{sessionId}/compare/{compareSessionId}/result` path allows you
    to get comparison results for Microsoft Entra ID items, initiated by a comparison session with the
    specified `sessionId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore
    Operator.</p>

    Args:
        session_id (UUID):
        compare_session_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[EntraIdTenantItemComparisonSessionModel, Error]]
    """

    kwargs = _get_kwargs(
        session_id=session_id,
        compare_session_id=compare_session_id,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    session_id: UUID,
    compare_session_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev0",
) -> Optional[Union[EntraIdTenantItemComparisonSessionModel, Error]]:
    """Get Comparison Results for Microsoft Entra ID Items

     The HTTP GET request to the
    `/api/v1/backupBrowser/entraIdTenant/{sessionId}/compare/{compareSessionId}/result` path allows you
    to get comparison results for Microsoft Entra ID items, initiated by a comparison session with the
    specified `sessionId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore
    Operator.</p>

    Args:
        session_id (UUID):
        compare_session_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[EntraIdTenantItemComparisonSessionModel, Error]
    """

    return sync_detailed(
        session_id=session_id,
        compare_session_id=compare_session_id,
        client=client,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    session_id: UUID,
    compare_session_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev0",
) -> Response[Union[EntraIdTenantItemComparisonSessionModel, Error]]:
    """Get Comparison Results for Microsoft Entra ID Items

     The HTTP GET request to the
    `/api/v1/backupBrowser/entraIdTenant/{sessionId}/compare/{compareSessionId}/result` path allows you
    to get comparison results for Microsoft Entra ID items, initiated by a comparison session with the
    specified `sessionId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore
    Operator.</p>

    Args:
        session_id (UUID):
        compare_session_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[EntraIdTenantItemComparisonSessionModel, Error]]
    """

    kwargs = _get_kwargs(
        session_id=session_id,
        compare_session_id=compare_session_id,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    session_id: UUID,
    compare_session_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev0",
) -> Optional[Union[EntraIdTenantItemComparisonSessionModel, Error]]:
    """Get Comparison Results for Microsoft Entra ID Items

     The HTTP GET request to the
    `/api/v1/backupBrowser/entraIdTenant/{sessionId}/compare/{compareSessionId}/result` path allows you
    to get comparison results for Microsoft Entra ID items, initiated by a comparison session with the
    specified `sessionId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore
    Operator.</p>

    Args:
        session_id (UUID):
        compare_session_id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[EntraIdTenantItemComparisonSessionModel, Error]
    """

    return (
        await asyncio_detailed(
            session_id=session_id,
            compare_session_id=compare_session_id,
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed
