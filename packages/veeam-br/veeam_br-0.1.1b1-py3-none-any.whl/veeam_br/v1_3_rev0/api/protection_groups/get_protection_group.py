from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.ad_objects_protection_group_model import ADObjectsProtectionGroupModel
from ...models.csv_file_protection_group_model import CSVFileProtectionGroupModel
from ...models.error import Error
from ...models.individual_computers_protection_group_model import IndividualComputersProtectionGroupModel
from ...models.manually_added_protection_group_model import ManuallyAddedProtectionGroupModel
from ...models.pre_installed_agents_protection_group_model import PreInstalledAgentsProtectionGroupModel
from ...types import Response


def _get_kwargs(
    id: UUID,
    *,
    x_api_version: str = "1.3-rev0",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/agents/protectionGroups/{id}",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        Error,
        Union[
            "ADObjectsProtectionGroupModel",
            "CSVFileProtectionGroupModel",
            "IndividualComputersProtectionGroupModel",
            "ManuallyAddedProtectionGroupModel",
            "PreInstalledAgentsProtectionGroupModel",
        ],
    ]
]:
    if response.status_code == 200:

        def _parse_response_200(
            data: object,
        ) -> Union[
            "ADObjectsProtectionGroupModel",
            "CSVFileProtectionGroupModel",
            "IndividualComputersProtectionGroupModel",
            "ManuallyAddedProtectionGroupModel",
            "PreInstalledAgentsProtectionGroupModel",
        ]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_protection_group_model_type_0 = ManuallyAddedProtectionGroupModel.from_dict(data)

                return componentsschemas_protection_group_model_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_protection_group_model_type_1 = IndividualComputersProtectionGroupModel.from_dict(
                    data
                )

                return componentsschemas_protection_group_model_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_protection_group_model_type_2 = ADObjectsProtectionGroupModel.from_dict(data)

                return componentsschemas_protection_group_model_type_2
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_protection_group_model_type_3 = CSVFileProtectionGroupModel.from_dict(data)

                return componentsschemas_protection_group_model_type_3
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_protection_group_model_type_4 = PreInstalledAgentsProtectionGroupModel.from_dict(data)

            return componentsschemas_protection_group_model_type_4

        response_200 = _parse_response_200(response.json())

        return response_200

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
            "ADObjectsProtectionGroupModel",
            "CSVFileProtectionGroupModel",
            "IndividualComputersProtectionGroupModel",
            "ManuallyAddedProtectionGroupModel",
            "PreInstalledAgentsProtectionGroupModel",
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
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev0",
) -> Response[
    Union[
        Error,
        Union[
            "ADObjectsProtectionGroupModel",
            "CSVFileProtectionGroupModel",
            "IndividualComputersProtectionGroupModel",
            "ManuallyAddedProtectionGroupModel",
            "PreInstalledAgentsProtectionGroupModel",
        ],
    ]
]:
    """Get Protection Group

     The HTTP GET request to the `/api/v1/agents/protectionGroups/{id}` path allows you to get a
    protection group that has the specified `id`. <p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['ADObjectsProtectionGroupModel', 'CSVFileProtectionGroupModel', 'IndividualComputersProtectionGroupModel', 'ManuallyAddedProtectionGroupModel', 'PreInstalledAgentsProtectionGroupModel']]]
    """

    kwargs = _get_kwargs(
        id=id,
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev0",
) -> Optional[
    Union[
        Error,
        Union[
            "ADObjectsProtectionGroupModel",
            "CSVFileProtectionGroupModel",
            "IndividualComputersProtectionGroupModel",
            "ManuallyAddedProtectionGroupModel",
            "PreInstalledAgentsProtectionGroupModel",
        ],
    ]
]:
    """Get Protection Group

     The HTTP GET request to the `/api/v1/agents/protectionGroups/{id}` path allows you to get a
    protection group that has the specified `id`. <p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['ADObjectsProtectionGroupModel', 'CSVFileProtectionGroupModel', 'IndividualComputersProtectionGroupModel', 'ManuallyAddedProtectionGroupModel', 'PreInstalledAgentsProtectionGroupModel']]
    """

    return sync_detailed(
        id=id,
        client=client,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev0",
) -> Response[
    Union[
        Error,
        Union[
            "ADObjectsProtectionGroupModel",
            "CSVFileProtectionGroupModel",
            "IndividualComputersProtectionGroupModel",
            "ManuallyAddedProtectionGroupModel",
            "PreInstalledAgentsProtectionGroupModel",
        ],
    ]
]:
    """Get Protection Group

     The HTTP GET request to the `/api/v1/agents/protectionGroups/{id}` path allows you to get a
    protection group that has the specified `id`. <p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['ADObjectsProtectionGroupModel', 'CSVFileProtectionGroupModel', 'IndividualComputersProtectionGroupModel', 'ManuallyAddedProtectionGroupModel', 'PreInstalledAgentsProtectionGroupModel']]]
    """

    kwargs = _get_kwargs(
        id=id,
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: UUID,
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev0",
) -> Optional[
    Union[
        Error,
        Union[
            "ADObjectsProtectionGroupModel",
            "CSVFileProtectionGroupModel",
            "IndividualComputersProtectionGroupModel",
            "ManuallyAddedProtectionGroupModel",
            "PreInstalledAgentsProtectionGroupModel",
        ],
    ]
]:
    """Get Protection Group

     The HTTP GET request to the `/api/v1/agents/protectionGroups/{id}` path allows you to get a
    protection group that has the specified `id`. <p>**Available to**&#58; Veeam Backup
    Administrator.</p>

    Args:
        id (UUID):
        x_api_version (str):  Default: '1.3-rev0'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['ADObjectsProtectionGroupModel', 'CSVFileProtectionGroupModel', 'IndividualComputersProtectionGroupModel', 'ManuallyAddedProtectionGroupModel', 'PreInstalledAgentsProtectionGroupModel']]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed
