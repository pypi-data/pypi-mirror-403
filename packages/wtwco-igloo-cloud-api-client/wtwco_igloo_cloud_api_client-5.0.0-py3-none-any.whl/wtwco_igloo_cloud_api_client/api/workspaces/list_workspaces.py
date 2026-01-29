from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.workspace_array_response import WorkspaceArrayResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    list_all: bool | Unset = False,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["list-all"] = list_all

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v3/workspaces",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | WorkspaceArrayResponse | None:
    if response.status_code == 200:
        response_200 = WorkspaceArrayResponse.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = cast(Any, None)
        return response_401

    if response.status_code == 403:
        response_403 = cast(Any, None)
        return response_403

    if response.status_code == 406:
        response_406 = cast(Any, None)
        return response_406

    if response.status_code == 415:
        response_415 = cast(Any, None)
        return response_415

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | WorkspaceArrayResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    list_all: bool | Unset = False,
) -> Response[Any | WorkspaceArrayResponse]:
    """Gets the list of all workspaces.

    Args:
        list_all (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | WorkspaceArrayResponse]
    """

    kwargs = _get_kwargs(
        list_all=list_all,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    list_all: bool | Unset = False,
) -> Any | WorkspaceArrayResponse | None:
    """Gets the list of all workspaces.

    Args:
        list_all (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | WorkspaceArrayResponse
    """

    return sync_detailed(
        client=client,
        list_all=list_all,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    list_all: bool | Unset = False,
) -> Response[Any | WorkspaceArrayResponse]:
    """Gets the list of all workspaces.

    Args:
        list_all (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | WorkspaceArrayResponse]
    """

    kwargs = _get_kwargs(
        list_all=list_all,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    list_all: bool | Unset = False,
) -> Any | WorkspaceArrayResponse | None:
    """Gets the list of all workspaces.

    Args:
        list_all (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | WorkspaceArrayResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            list_all=list_all,
        )
    ).parsed
