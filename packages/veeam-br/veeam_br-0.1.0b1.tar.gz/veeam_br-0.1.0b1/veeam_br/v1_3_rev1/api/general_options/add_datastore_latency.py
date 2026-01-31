from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.datastores_latency_settings_model import DatastoresLatencySettingsModel
from ...models.datastores_latency_settings_spec import DatastoresLatencySettingsSpec
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    *,
    body: DatastoresLatencySettingsSpec,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/generalOptions/storageLatency/datastores",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[DatastoresLatencySettingsModel, Error]]:
    if response.status_code == 201:
        response_201 = DatastoresLatencySettingsModel.from_dict(response.json())

        return response_201

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
) -> Response[Union[DatastoresLatencySettingsModel, Error]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: DatastoresLatencySettingsSpec,
    x_api_version: str = "1.3-rev1",
) -> Response[Union[DatastoresLatencySettingsModel, Error]]:
    """Add Latency Settings for Specific Datastore

     The HTTP POST request to the `/api/v1/generalOptions/storageLatency/datastores` endpoint adds custom
    latency settings for a specific datastore.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (DatastoresLatencySettingsSpec): Datastore latency settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DatastoresLatencySettingsModel, Error]]
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
    body: DatastoresLatencySettingsSpec,
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[DatastoresLatencySettingsModel, Error]]:
    """Add Latency Settings for Specific Datastore

     The HTTP POST request to the `/api/v1/generalOptions/storageLatency/datastores` endpoint adds custom
    latency settings for a specific datastore.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (DatastoresLatencySettingsSpec): Datastore latency settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DatastoresLatencySettingsModel, Error]
    """

    return sync_detailed(
        client=client,
        body=body,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: DatastoresLatencySettingsSpec,
    x_api_version: str = "1.3-rev1",
) -> Response[Union[DatastoresLatencySettingsModel, Error]]:
    """Add Latency Settings for Specific Datastore

     The HTTP POST request to the `/api/v1/generalOptions/storageLatency/datastores` endpoint adds custom
    latency settings for a specific datastore.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (DatastoresLatencySettingsSpec): Datastore latency settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DatastoresLatencySettingsModel, Error]]
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
    body: DatastoresLatencySettingsSpec,
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[DatastoresLatencySettingsModel, Error]]:
    """Add Latency Settings for Specific Datastore

     The HTTP POST request to the `/api/v1/generalOptions/storageLatency/datastores` endpoint adds custom
    latency settings for a specific datastore.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.
        body (DatastoresLatencySettingsSpec): Datastore latency settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DatastoresLatencySettingsModel, Error]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_version=x_api_version,
        )
    ).parsed
