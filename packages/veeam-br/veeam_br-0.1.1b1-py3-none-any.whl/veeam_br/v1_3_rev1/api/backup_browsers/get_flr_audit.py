from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.flr_audit_mount_model import FlrAuditMountModel
from ...types import Response


def _get_kwargs(
    session_id: UUID,
    *,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/backupBrowser/flr/{session_id}/audit",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, FlrAuditMountModel]]:
    if response.status_code == 200:
        response_200 = FlrAuditMountModel.from_dict(response.json())

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
) -> Response[Union[Error, FlrAuditMountModel]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    session_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev1",
) -> Response[Union[Error, FlrAuditMountModel]]:
    """Get Restored Files Audit

     The HTTP GET request to the `/api/v1/backupBrowser/flr/{sessionId}/audit` endpoint gets an
    aggregated view of items restored during a restore session that has the specified
    `sessionId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, FlrAuditMountModel]]
    """

    kwargs = _get_kwargs(
        session_id=session_id,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    session_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[Error, FlrAuditMountModel]]:
    """Get Restored Files Audit

     The HTTP GET request to the `/api/v1/backupBrowser/flr/{sessionId}/audit` endpoint gets an
    aggregated view of items restored during a restore session that has the specified
    `sessionId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, FlrAuditMountModel]
    """

    return sync_detailed(
        session_id=session_id,
        client=client,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    session_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev1",
) -> Response[Union[Error, FlrAuditMountModel]]:
    """Get Restored Files Audit

     The HTTP GET request to the `/api/v1/backupBrowser/flr/{sessionId}/audit` endpoint gets an
    aggregated view of items restored during a restore session that has the specified
    `sessionId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, FlrAuditMountModel]]
    """

    kwargs = _get_kwargs(
        session_id=session_id,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    session_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[Error, FlrAuditMountModel]]:
    """Get Restored Files Audit

     The HTTP GET request to the `/api/v1/backupBrowser/flr/{sessionId}/audit` endpoint gets an
    aggregated view of items restored during a restore session that has the specified
    `sessionId`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, FlrAuditMountModel]
    """

    return (
        await asyncio_detailed(
            session_id=session_id,
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed
