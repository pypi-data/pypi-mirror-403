from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.common_task_model import CommonTaskModel
from ...models.deployment_kit_task_model import DeploymentKitTaskModel
from ...models.error import Error
from ...models.flr_download_task_model import FlrDownloadTaskModel
from ...models.flr_restore_task_model import FlrRestoreTaskModel
from ...models.flr_search_task_model import FlrSearchTaskModel
from ...models.hierarchy_rescan_task_model import HierarchyRescanTaskModel
from ...types import Response


def _get_kwargs(
    hostname: str,
    *,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v1/inventory/{hostname}/rescan",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        Error,
        Union[
            "CommonTaskModel",
            "DeploymentKitTaskModel",
            "FlrDownloadTaskModel",
            "FlrRestoreTaskModel",
            "FlrSearchTaskModel",
            "HierarchyRescanTaskModel",
        ],
    ]
]:
    if response.status_code == 201:

        def _parse_response_201(
            data: object,
        ) -> Union[
            "CommonTaskModel",
            "DeploymentKitTaskModel",
            "FlrDownloadTaskModel",
            "FlrRestoreTaskModel",
            "FlrSearchTaskModel",
            "HierarchyRescanTaskModel",
        ]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_task_model_type_0 = CommonTaskModel.from_dict(data)

                return componentsschemas_task_model_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_task_model_type_1 = FlrRestoreTaskModel.from_dict(data)

                return componentsschemas_task_model_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_task_model_type_2 = FlrDownloadTaskModel.from_dict(data)

                return componentsschemas_task_model_type_2
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_task_model_type_3 = FlrSearchTaskModel.from_dict(data)

                return componentsschemas_task_model_type_3
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_task_model_type_4 = HierarchyRescanTaskModel.from_dict(data)

                return componentsschemas_task_model_type_4
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_task_model_type_5 = DeploymentKitTaskModel.from_dict(data)

            return componentsschemas_task_model_type_5

        response_201 = _parse_response_201(response.json())

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
) -> Response[
    Union[
        Error,
        Union[
            "CommonTaskModel",
            "DeploymentKitTaskModel",
            "FlrDownloadTaskModel",
            "FlrRestoreTaskModel",
            "FlrSearchTaskModel",
            "HierarchyRescanTaskModel",
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
    hostname: str,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev1",
) -> Response[
    Union[
        Error,
        Union[
            "CommonTaskModel",
            "DeploymentKitTaskModel",
            "FlrDownloadTaskModel",
            "FlrRestoreTaskModel",
            "FlrSearchTaskModel",
            "HierarchyRescanTaskModel",
        ],
    ]
]:
    """Rescan Inventory Objects

     The HTTP POST request to the `/api/v1/inventory/{hostname}/rescan` endpoint rescans inventory
    objects of a virtualization server (or host) that has the specified `hostname`.<p>**Available
    to**&#58; Veeam Backup Administrator.</p>

    Args:
        hostname (str):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['CommonTaskModel', 'DeploymentKitTaskModel', 'FlrDownloadTaskModel', 'FlrRestoreTaskModel', 'FlrSearchTaskModel', 'HierarchyRescanTaskModel']]]
    """

    kwargs = _get_kwargs(
        hostname=hostname,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    hostname: str,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev1",
) -> Optional[
    Union[
        Error,
        Union[
            "CommonTaskModel",
            "DeploymentKitTaskModel",
            "FlrDownloadTaskModel",
            "FlrRestoreTaskModel",
            "FlrSearchTaskModel",
            "HierarchyRescanTaskModel",
        ],
    ]
]:
    """Rescan Inventory Objects

     The HTTP POST request to the `/api/v1/inventory/{hostname}/rescan` endpoint rescans inventory
    objects of a virtualization server (or host) that has the specified `hostname`.<p>**Available
    to**&#58; Veeam Backup Administrator.</p>

    Args:
        hostname (str):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['CommonTaskModel', 'DeploymentKitTaskModel', 'FlrDownloadTaskModel', 'FlrRestoreTaskModel', 'FlrSearchTaskModel', 'HierarchyRescanTaskModel']]
    """

    return sync_detailed(
        hostname=hostname,
        client=client,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    hostname: str,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev1",
) -> Response[
    Union[
        Error,
        Union[
            "CommonTaskModel",
            "DeploymentKitTaskModel",
            "FlrDownloadTaskModel",
            "FlrRestoreTaskModel",
            "FlrSearchTaskModel",
            "HierarchyRescanTaskModel",
        ],
    ]
]:
    """Rescan Inventory Objects

     The HTTP POST request to the `/api/v1/inventory/{hostname}/rescan` endpoint rescans inventory
    objects of a virtualization server (or host) that has the specified `hostname`.<p>**Available
    to**&#58; Veeam Backup Administrator.</p>

    Args:
        hostname (str):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['CommonTaskModel', 'DeploymentKitTaskModel', 'FlrDownloadTaskModel', 'FlrRestoreTaskModel', 'FlrSearchTaskModel', 'HierarchyRescanTaskModel']]]
    """

    kwargs = _get_kwargs(
        hostname=hostname,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    hostname: str,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev1",
) -> Optional[
    Union[
        Error,
        Union[
            "CommonTaskModel",
            "DeploymentKitTaskModel",
            "FlrDownloadTaskModel",
            "FlrRestoreTaskModel",
            "FlrSearchTaskModel",
            "HierarchyRescanTaskModel",
        ],
    ]
]:
    """Rescan Inventory Objects

     The HTTP POST request to the `/api/v1/inventory/{hostname}/rescan` endpoint rescans inventory
    objects of a virtualization server (or host) that has the specified `hostname`.<p>**Available
    to**&#58; Veeam Backup Administrator.</p>

    Args:
        hostname (str):
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['CommonTaskModel', 'DeploymentKitTaskModel', 'FlrDownloadTaskModel', 'FlrRestoreTaskModel', 'FlrSearchTaskModel', 'HierarchyRescanTaskModel']]
    """

    return (
        await asyncio_detailed(
            hostname=hostname,
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed
