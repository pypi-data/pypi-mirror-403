from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.general_options_gmail_server_settings_model import GeneralOptionsGmailServerSettingsModel
from ...models.general_options_ms365_server_settings_model import GeneralOptionsMS365ServerSettingsModel
from ...models.general_options_smtp_server_settings_model import GeneralOptionsSMTPServerSettingsModel
from ...types import Response


def _get_kwargs(
    *,
    x_api_version: str = "1.3-rev1",
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-version"] = x_api_version

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/generalOptions/emailSettings",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        Error,
        Union[
            "GeneralOptionsGmailServerSettingsModel",
            "GeneralOptionsMS365ServerSettingsModel",
            "GeneralOptionsSMTPServerSettingsModel",
        ],
    ]
]:
    if response.status_code == 200:

        def _parse_response_200(
            data: object,
        ) -> Union[
            "GeneralOptionsGmailServerSettingsModel",
            "GeneralOptionsMS365ServerSettingsModel",
            "GeneralOptionsSMTPServerSettingsModel",
        ]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_general_options_email_settings_base_model_type_0 = (
                    GeneralOptionsSMTPServerSettingsModel.from_dict(data)
                )

                return componentsschemas_general_options_email_settings_base_model_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_general_options_email_settings_base_model_type_1 = (
                    GeneralOptionsGmailServerSettingsModel.from_dict(data)
                )

                return componentsschemas_general_options_email_settings_base_model_type_1
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_general_options_email_settings_base_model_type_2 = (
                GeneralOptionsMS365ServerSettingsModel.from_dict(data)
            )

            return componentsschemas_general_options_email_settings_base_model_type_2

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
            "GeneralOptionsGmailServerSettingsModel",
            "GeneralOptionsMS365ServerSettingsModel",
            "GeneralOptionsSMTPServerSettingsModel",
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
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev1",
) -> Response[
    Union[
        Error,
        Union[
            "GeneralOptionsGmailServerSettingsModel",
            "GeneralOptionsMS365ServerSettingsModel",
            "GeneralOptionsSMTPServerSettingsModel",
        ],
    ]
]:
    """Get Email Settings

     The HTTP GET request to the `/api/v1/generalOptions/emailSettings` endpoint gets Veeam Backup &
    Replication email settings.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['GeneralOptionsGmailServerSettingsModel', 'GeneralOptionsMS365ServerSettingsModel', 'GeneralOptionsSMTPServerSettingsModel']]]
    """

    kwargs = _get_kwargs(
        x_api_version=x_api_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev1",
) -> Optional[
    Union[
        Error,
        Union[
            "GeneralOptionsGmailServerSettingsModel",
            "GeneralOptionsMS365ServerSettingsModel",
            "GeneralOptionsSMTPServerSettingsModel",
        ],
    ]
]:
    """Get Email Settings

     The HTTP GET request to the `/api/v1/generalOptions/emailSettings` endpoint gets Veeam Backup &
    Replication email settings.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['GeneralOptionsGmailServerSettingsModel', 'GeneralOptionsMS365ServerSettingsModel', 'GeneralOptionsSMTPServerSettingsModel']]
    """

    return sync_detailed(
        client=client,
        x_api_version=x_api_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev1",
) -> Response[
    Union[
        Error,
        Union[
            "GeneralOptionsGmailServerSettingsModel",
            "GeneralOptionsMS365ServerSettingsModel",
            "GeneralOptionsSMTPServerSettingsModel",
        ],
    ]
]:
    """Get Email Settings

     The HTTP GET request to the `/api/v1/generalOptions/emailSettings` endpoint gets Veeam Backup &
    Replication email settings.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Union['GeneralOptionsGmailServerSettingsModel', 'GeneralOptionsMS365ServerSettingsModel', 'GeneralOptionsSMTPServerSettingsModel']]]
    """

    kwargs = _get_kwargs(
        x_api_version=x_api_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    x_api_version: str = "1.3-rev1",
) -> Optional[
    Union[
        Error,
        Union[
            "GeneralOptionsGmailServerSettingsModel",
            "GeneralOptionsMS365ServerSettingsModel",
            "GeneralOptionsSMTPServerSettingsModel",
        ],
    ]
]:
    """Get Email Settings

     The HTTP GET request to the `/api/v1/generalOptions/emailSettings` endpoint gets Veeam Backup &
    Replication email settings.<p>**Available to**&#58; Veeam Backup Administrator.</p>

    Args:
        x_api_version (str):  Default: '1.3-rev1'.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Union['GeneralOptionsGmailServerSettingsModel', 'GeneralOptionsMS365ServerSettingsModel', 'GeneralOptionsSMTPServerSettingsModel']]
    """

    return (
        await asyncio_detailed(
            client=client,
            x_api_version=x_api_version,
        )
    ).parsed
