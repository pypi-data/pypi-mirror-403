from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.aws_machines_browser_model import AWSMachinesBrowserModel
from ...models.aws_machines_browser_spec import AWSMachinesBrowserSpec
from ...models.azure_machines_browser_model import AzureMachinesBrowserModel
from ...models.azure_machines_browser_spec import AzureMachinesBrowserSpec
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: Union["AWSMachinesBrowserSpec", "AzureMachinesBrowserSpec"],
    reset_cache: Union[Unset, bool] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    params: dict[str, Any] = {}

    params["resetCache"] = reset_cache

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/cloudBrowser/virtualMachines",
        "params": params,
    }

    _kwargs["json"]: dict[str, Any]
    if isinstance(body, AzureMachinesBrowserSpec):
        _kwargs["json"] = body.to_dict()
    else:
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, Union["AWSMachinesBrowserModel", "AzureMachinesBrowserModel"]]]:
    if response.status_code == 200:

        def _parse_response_200(data: object) -> Union["AWSMachinesBrowserModel", "AzureMachinesBrowserModel"]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_cloud_browser_virtual_machines_model_type_0 = AzureMachinesBrowserModel.from_dict(
                    data
                )

                return componentsschemas_cloud_browser_virtual_machines_model_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_cloud_browser_virtual_machines_model_type_1 = AWSMachinesBrowserModel.from_dict(data)

            return componentsschemas_cloud_browser_virtual_machines_model_type_1

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
) -> Response[Union[Error, Union["AWSMachinesBrowserModel", "AzureMachinesBrowserModel"]]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union["AWSMachinesBrowserSpec", "AzureMachinesBrowserSpec"],
    reset_cache: Union[Unset, bool] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[Union[Error, Union["AWSMachinesBrowserModel", "AzureMachinesBrowserModel"]]]:
    """Get Cloud Virtual Machines

     The HTTP POST request to the `/api/v1/cloudBrowser/virtualMachines` endpoint browses cloud virtual
    machines available for the specified storage account.<p>To reduce the response time and the number
    of records in the response, use the available filtering in the request body.<p>**Available to**&#58;
    Veeam Backup Administrator.</p>

    Args:
        reset_cache (Union[Unset, bool]):
        x_api_version (str):  Default: '1.3-rev1'.
        body (Union['AWSMachinesBrowserSpec', 'AzureMachinesBrowserSpec']): Cloud resource
            settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['AWSMachinesBrowserModel', 'AzureMachinesBrowserModel']]]
    """

    kwargs = _get_kwargs(
        body=body,
        reset_cache=reset_cache,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union["AWSMachinesBrowserSpec", "AzureMachinesBrowserSpec"],
    reset_cache: Union[Unset, bool] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[Error, Union["AWSMachinesBrowserModel", "AzureMachinesBrowserModel"]]]:
    """Get Cloud Virtual Machines

     The HTTP POST request to the `/api/v1/cloudBrowser/virtualMachines` endpoint browses cloud virtual
    machines available for the specified storage account.<p>To reduce the response time and the number
    of records in the response, use the available filtering in the request body.<p>**Available to**&#58;
    Veeam Backup Administrator.</p>

    Args:
        reset_cache (Union[Unset, bool]):
        x_api_version (str):  Default: '1.3-rev1'.
        body (Union['AWSMachinesBrowserSpec', 'AzureMachinesBrowserSpec']): Cloud resource
            settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['AWSMachinesBrowserModel', 'AzureMachinesBrowserModel']]
    """

    return sync_detailed(
        client=client,
        body=body,
        reset_cache=reset_cache,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union["AWSMachinesBrowserSpec", "AzureMachinesBrowserSpec"],
    reset_cache: Union[Unset, bool] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Response[Union[Error, Union["AWSMachinesBrowserModel", "AzureMachinesBrowserModel"]]]:
    """Get Cloud Virtual Machines

     The HTTP POST request to the `/api/v1/cloudBrowser/virtualMachines` endpoint browses cloud virtual
    machines available for the specified storage account.<p>To reduce the response time and the number
    of records in the response, use the available filtering in the request body.<p>**Available to**&#58;
    Veeam Backup Administrator.</p>

    Args:
        reset_cache (Union[Unset, bool]):
        x_api_version (str):  Default: '1.3-rev1'.
        body (Union['AWSMachinesBrowserSpec', 'AzureMachinesBrowserSpec']): Cloud resource
            settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['AWSMachinesBrowserModel', 'AzureMachinesBrowserModel']]]
    """

    kwargs = _get_kwargs(
        body=body,
        reset_cache=reset_cache,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: Union["AWSMachinesBrowserSpec", "AzureMachinesBrowserSpec"],
    reset_cache: Union[Unset, bool] = UNSET,
    x_api_version: str = "1.3-rev1",
) -> Optional[Union[Error, Union["AWSMachinesBrowserModel", "AzureMachinesBrowserModel"]]]:
    """Get Cloud Virtual Machines

     The HTTP POST request to the `/api/v1/cloudBrowser/virtualMachines` endpoint browses cloud virtual
    machines available for the specified storage account.<p>To reduce the response time and the number
    of records in the response, use the available filtering in the request body.<p>**Available to**&#58;
    Veeam Backup Administrator.</p>

    Args:
        reset_cache (Union[Unset, bool]):
        x_api_version (str):  Default: '1.3-rev1'.
        body (Union['AWSMachinesBrowserSpec', 'AzureMachinesBrowserSpec']): Cloud resource
            settings.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['AWSMachinesBrowserModel', 'AzureMachinesBrowserModel']]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            reset_cache=reset_cache,
            x_api_version=x_api_version,
        )
    ).parsed
