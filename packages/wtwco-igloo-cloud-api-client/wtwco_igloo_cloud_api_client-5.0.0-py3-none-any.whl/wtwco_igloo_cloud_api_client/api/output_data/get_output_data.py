from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.output_data_response import OutputDataResponse
from ...models.response_wrapper import ResponseWrapper
from ...types import UNSET, Response, Unset


def _get_kwargs(
    workspace_id: int,
    project_id: int,
    run_id: int,
    *,
    table_name: str | Unset = UNSET,
    pool: str | Unset = UNSET,
    pool_id: int | Unset = UNSET,
    wait_seconds: int | Unset = 0,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["table-name"] = table_name

    params["pool"] = pool

    params["pool-id"] = pool_id

    params["wait-seconds"] = wait_seconds

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v3/workspaces/{workspace_id}/projects/{project_id}/runs/{run_id}/output-data",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | OutputDataResponse | ResponseWrapper | None:
    if response.status_code == 200:
        response_200 = OutputDataResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ResponseWrapper.from_dict(response.json())

        return response_400

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

    if response.status_code == 415:
        response_415 = cast(Any, None)
        return response_415

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | OutputDataResponse | ResponseWrapper]:
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
    *,
    client: AuthenticatedClient | Client,
    table_name: str | Unset = UNSET,
    pool: str | Unset = UNSET,
    pool_id: int | Unset = UNSET,
    wait_seconds: int | Unset = 0,
) -> Response[Any | OutputDataResponse | ResponseWrapper]:
    """Gets the output data in a table for a run, this will force a run to be calculated if necessary by
    submitting a job to Igloo Cloud Compute.

    Args:
        workspace_id (int):
        project_id (int):
        run_id (int):
        table_name (str | Unset):
        pool (str | Unset):
        pool_id (int | Unset):
        wait_seconds (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | OutputDataResponse | ResponseWrapper]
    """

    kwargs = _get_kwargs(
        workspace_id=workspace_id,
        project_id=project_id,
        run_id=run_id,
        table_name=table_name,
        pool=pool,
        pool_id=pool_id,
        wait_seconds=wait_seconds,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    workspace_id: int,
    project_id: int,
    run_id: int,
    *,
    client: AuthenticatedClient | Client,
    table_name: str | Unset = UNSET,
    pool: str | Unset = UNSET,
    pool_id: int | Unset = UNSET,
    wait_seconds: int | Unset = 0,
) -> Any | OutputDataResponse | ResponseWrapper | None:
    """Gets the output data in a table for a run, this will force a run to be calculated if necessary by
    submitting a job to Igloo Cloud Compute.

    Args:
        workspace_id (int):
        project_id (int):
        run_id (int):
        table_name (str | Unset):
        pool (str | Unset):
        pool_id (int | Unset):
        wait_seconds (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | OutputDataResponse | ResponseWrapper
    """

    return sync_detailed(
        workspace_id=workspace_id,
        project_id=project_id,
        run_id=run_id,
        client=client,
        table_name=table_name,
        pool=pool,
        pool_id=pool_id,
        wait_seconds=wait_seconds,
    ).parsed


async def asyncio_detailed(
    workspace_id: int,
    project_id: int,
    run_id: int,
    *,
    client: AuthenticatedClient | Client,
    table_name: str | Unset = UNSET,
    pool: str | Unset = UNSET,
    pool_id: int | Unset = UNSET,
    wait_seconds: int | Unset = 0,
) -> Response[Any | OutputDataResponse | ResponseWrapper]:
    """Gets the output data in a table for a run, this will force a run to be calculated if necessary by
    submitting a job to Igloo Cloud Compute.

    Args:
        workspace_id (int):
        project_id (int):
        run_id (int):
        table_name (str | Unset):
        pool (str | Unset):
        pool_id (int | Unset):
        wait_seconds (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | OutputDataResponse | ResponseWrapper]
    """

    kwargs = _get_kwargs(
        workspace_id=workspace_id,
        project_id=project_id,
        run_id=run_id,
        table_name=table_name,
        pool=pool,
        pool_id=pool_id,
        wait_seconds=wait_seconds,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace_id: int,
    project_id: int,
    run_id: int,
    *,
    client: AuthenticatedClient | Client,
    table_name: str | Unset = UNSET,
    pool: str | Unset = UNSET,
    pool_id: int | Unset = UNSET,
    wait_seconds: int | Unset = 0,
) -> Any | OutputDataResponse | ResponseWrapper | None:
    """Gets the output data in a table for a run, this will force a run to be calculated if necessary by
    submitting a job to Igloo Cloud Compute.

    Args:
        workspace_id (int):
        project_id (int):
        run_id (int):
        table_name (str | Unset):
        pool (str | Unset):
        pool_id (int | Unset):
        wait_seconds (int | Unset):  Default: 0.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | OutputDataResponse | ResponseWrapper
    """

    return (
        await asyncio_detailed(
            workspace_id=workspace_id,
            project_id=project_id,
            run_id=run_id,
            client=client,
            table_name=table_name,
            pool=pool,
            pool_id=pool_id,
            wait_seconds=wait_seconds,
        )
    ).parsed
