from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.input_data_response import InputDataResponse
from ...models.response_wrapper import ResponseWrapper
from ...types import Response


def _get_kwargs(
    workspace_id: int,
    project_id: int,
    run_id: int,
    data_table_name: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v3/workspaces/{workspace_id}/projects/{project_id}/runs/{run_id}/input-data/{data_table_name}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | InputDataResponse | ResponseWrapper | None:
    if response.status_code == 200:
        response_200 = InputDataResponse.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = cast(Any, None)
        return response_401

    if response.status_code == 403:
        response_403 = cast(Any, None)
        return response_403

    if response.status_code == 404:
        response_404 = ResponseWrapper.from_dict(response.json())

        return response_404

    if response.status_code == 406:
        response_406 = cast(Any, None)
        return response_406

    if response.status_code == 409:
        response_409 = ResponseWrapper.from_dict(response.json())

        return response_409

    if response.status_code == 415:
        response_415 = cast(Any, None)
        return response_415

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | InputDataResponse | ResponseWrapper]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    workspace_id: int,
    project_id: int,
    run_id: int,
    data_table_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | InputDataResponse | ResponseWrapper]:
    """Get the input data in a table for a run.

    Args:
        workspace_id (int):
        project_id (int):
        run_id (int):
        data_table_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | InputDataResponse | ResponseWrapper]
    """

    kwargs = _get_kwargs(
        workspace_id=workspace_id,
        project_id=project_id,
        run_id=run_id,
        data_table_name=data_table_name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    workspace_id: int,
    project_id: int,
    run_id: int,
    data_table_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Any | InputDataResponse | ResponseWrapper | None:
    """Get the input data in a table for a run.

    Args:
        workspace_id (int):
        project_id (int):
        run_id (int):
        data_table_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | InputDataResponse | ResponseWrapper
    """

    return sync_detailed(
        workspace_id=workspace_id,
        project_id=project_id,
        run_id=run_id,
        data_table_name=data_table_name,
        client=client,
    ).parsed


async def asyncio_detailed(
    workspace_id: int,
    project_id: int,
    run_id: int,
    data_table_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | InputDataResponse | ResponseWrapper]:
    """Get the input data in a table for a run.

    Args:
        workspace_id (int):
        project_id (int):
        run_id (int):
        data_table_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | InputDataResponse | ResponseWrapper]
    """

    kwargs = _get_kwargs(
        workspace_id=workspace_id,
        project_id=project_id,
        run_id=run_id,
        data_table_name=data_table_name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace_id: int,
    project_id: int,
    run_id: int,
    data_table_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Any | InputDataResponse | ResponseWrapper | None:
    """Get the input data in a table for a run.

    Args:
        workspace_id (int):
        project_id (int):
        run_id (int):
        data_table_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | InputDataResponse | ResponseWrapper
    """

    return (
        await asyncio_detailed(
            workspace_id=workspace_id,
            project_id=project_id,
            run_id=run_id,
            data_table_name=data_table_name,
            client=client,
        )
    ).parsed
