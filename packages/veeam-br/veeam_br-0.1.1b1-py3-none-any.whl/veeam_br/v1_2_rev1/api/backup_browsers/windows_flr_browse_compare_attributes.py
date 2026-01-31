from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.flr_compare_attributes_model import FlrCompareAttributesModel
from ...models.flr_compare_attributes_spec import FlrCompareAttributesSpec
from ...types import Response


def _get_kwargs(
    session_id: UUID,
    *,
    body: FlrCompareAttributesSpec,
    x_api_version: str = "1.2-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v1/backupBrowser/flr/{session_id}/compareAttributes",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, FlrCompareAttributesModel]]:
    if response.status_code == 200:
        response_200 = FlrCompareAttributesModel.from_dict(response.json())

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

    if response.status_code == 405:
        response_405 = Error.from_dict(response.json())

        return response_405

    if response.status_code == 500:
        response_500 = Error.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, FlrCompareAttributesModel]]:
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
    body: FlrCompareAttributesSpec,
    x_api_version: str = "1.2-rev1",
) -> Response[Union[Error, FlrCompareAttributesModel]]:
    r"""Compare Attributes

     The HTTP POST request to the `/api/v1/backupBrowser/flr/{sessionId}/compareAttributes` path allows
    you to compare attributes of file system items (drives, folders, files and links) from a restore
    session that has the specified `sessionId` with attributes of original items. <p> <div
    class=\"note\"><strong>NOTE</strong><br>The operation is allowed for Microsoft Windows machines
    only.</div><p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (FlrCompareAttributesSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, FlrCompareAttributesModel]]
    """

    kwargs = _get_kwargs(
        session_id=session_id,
        body=body,
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
    body: FlrCompareAttributesSpec,
    x_api_version: str = "1.2-rev1",
) -> Optional[Union[Error, FlrCompareAttributesModel]]:
    r"""Compare Attributes

     The HTTP POST request to the `/api/v1/backupBrowser/flr/{sessionId}/compareAttributes` path allows
    you to compare attributes of file system items (drives, folders, files and links) from a restore
    session that has the specified `sessionId` with attributes of original items. <p> <div
    class=\"note\"><strong>NOTE</strong><br>The operation is allowed for Microsoft Windows machines
    only.</div><p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (FlrCompareAttributesSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, FlrCompareAttributesModel]
    """

    return sync_detailed(
        session_id=session_id,
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    session_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: FlrCompareAttributesSpec,
    x_api_version: str = "1.2-rev1",
) -> Response[Union[Error, FlrCompareAttributesModel]]:
    r"""Compare Attributes

     The HTTP POST request to the `/api/v1/backupBrowser/flr/{sessionId}/compareAttributes` path allows
    you to compare attributes of file system items (drives, folders, files and links) from a restore
    session that has the specified `sessionId` with attributes of original items. <p> <div
    class=\"note\"><strong>NOTE</strong><br>The operation is allowed for Microsoft Windows machines
    only.</div><p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (FlrCompareAttributesSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, FlrCompareAttributesModel]]
    """

    kwargs = _get_kwargs(
        session_id=session_id,
        body=body,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    session_id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    body: FlrCompareAttributesSpec,
    x_api_version: str = "1.2-rev1",
) -> Optional[Union[Error, FlrCompareAttributesModel]]:
    r"""Compare Attributes

     The HTTP POST request to the `/api/v1/backupBrowser/flr/{sessionId}/compareAttributes` path allows
    you to compare attributes of file system items (drives, folders, files and links) from a restore
    session that has the specified `sessionId` with attributes of original items. <p> <div
    class=\"note\"><strong>NOTE</strong><br>The operation is allowed for Microsoft Windows machines
    only.</div><p>**Available to**&#58; Veeam Backup Administrator, Veeam Restore Operator.</p>

    Args:
        session_id (UUID):
        x_api_version (str):  Default: '1.2-rev1'.
        body (FlrCompareAttributesSpec):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, FlrCompareAttributesModel]
    """

    return (
        await asyncio_detailed(
            session_id=session_id,
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed
