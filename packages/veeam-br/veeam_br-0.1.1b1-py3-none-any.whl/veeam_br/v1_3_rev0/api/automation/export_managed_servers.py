from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.manage_server_export_spec import ManageServerExportSpec
from ...models.manage_server_import_spec_collection import ManageServerImportSpecCollection
from ...types import Response


def _get_kwargs(
    *,
    body: ManageServerExportSpec,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/automation/managedServers/export",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, ManageServerImportSpecCollection]]:
    if response.status_code == 200:
        response_200 = ManageServerImportSpecCollection.from_dict(response.json())

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
) -> Response[Union[Error, ManageServerImportSpecCollection]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ManageServerExportSpec,
    x_api_version: str = "1.3-rev0",
) -> Response[Union[Error, ManageServerImportSpecCollection]]:
    """Export Servers

     The HTTP POST request to the `/api/v1/automation/managedServers/export` path allows you to export
    managed servers from Veeam Backup & Replication.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (ManageServerExportSpec): Settings for exporting managed servers.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, ManageServerImportSpecCollection]]
    """

    kwargs = _get_kwargs(
        body=body,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ManageServerExportSpec,
    x_api_version: str = "1.3-rev0",
) -> Optional[Union[Error, ManageServerImportSpecCollection]]:
    """Export Servers

     The HTTP POST request to the `/api/v1/automation/managedServers/export` path allows you to export
    managed servers from Veeam Backup & Replication.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (ManageServerExportSpec): Settings for exporting managed servers.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, ManageServerImportSpecCollection]
    """

    return sync_detailed(
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ManageServerExportSpec,
    x_api_version: str = "1.3-rev0",
) -> Response[Union[Error, ManageServerImportSpecCollection]]:
    """Export Servers

     The HTTP POST request to the `/api/v1/automation/managedServers/export` path allows you to export
    managed servers from Veeam Backup & Replication.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (ManageServerExportSpec): Settings for exporting managed servers.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, ManageServerImportSpecCollection]]
    """

    kwargs = _get_kwargs(
        body=body,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ManageServerExportSpec,
    x_api_version: str = "1.3-rev0",
) -> Optional[Union[Error, ManageServerImportSpecCollection]]:
    """Export Servers

     The HTTP POST request to the `/api/v1/automation/managedServers/export` path allows you to export
    managed servers from Veeam Backup & Replication.<p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev0'.
        body (ManageServerExportSpec): Settings for exporting managed servers.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, ManageServerImportSpecCollection]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed
