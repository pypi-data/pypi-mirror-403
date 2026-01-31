from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    verification_code: str,
    *,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v1/cloudCredentials/appRegistration/{verification_code}",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Optional[Error]:
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


def _build_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Response[Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    verification_code: str,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev0",
) -> Response[Error]:
    """Register Microsoft Entra ID Application

     The HTTP POST request to the `/api/v1/cloudCredentials/appRegistration/{verificationCode}` path
    allows you to register a new Microsoft Entra ID application using the specified
    `verificationCode`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Security
    Administrator.</p>

    Args:
        verification_code (str):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error]
    """

    kwargs = _get_kwargs(
        verification_code=verification_code,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    verification_code: str,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev0",
) -> Optional[Error]:
    """Register Microsoft Entra ID Application

     The HTTP POST request to the `/api/v1/cloudCredentials/appRegistration/{verificationCode}` path
    allows you to register a new Microsoft Entra ID application using the specified
    `verificationCode`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Security
    Administrator.</p>

    Args:
        verification_code (str):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error
    """

    return sync_detailed(
        verification_code=verification_code,
        client=client,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    verification_code: str,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev0",
) -> Response[Error]:
    """Register Microsoft Entra ID Application

     The HTTP POST request to the `/api/v1/cloudCredentials/appRegistration/{verificationCode}` path
    allows you to register a new Microsoft Entra ID application using the specified
    `verificationCode`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Security
    Administrator.</p>

    Args:
        verification_code (str):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error]
    """

    kwargs = _get_kwargs(
        verification_code=verification_code,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    verification_code: str,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev0",
) -> Optional[Error]:
    """Register Microsoft Entra ID Application

     The HTTP POST request to the `/api/v1/cloudCredentials/appRegistration/{verificationCode}` path
    allows you to register a new Microsoft Entra ID application using the specified
    `verificationCode`.<p>**Available to**&#58; Veeam Backup Administrator, Veeam Security
    Administrator.</p>

    Args:
        verification_code (str):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error
    """

    return (
        await asyncio_detailed(
            verification_code=verification_code,
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed
