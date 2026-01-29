from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.data_table_include import DataTableInclude
from ...models.response_wrapper import ResponseWrapper
from ...models.table_data_response import TableDataResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    workspace_id: int,
    project_id: int,
    run_id: int,
    run_result_name: str,
    result_table_name: str,
    *,
    job_id: int | Unset = UNSET,
    include: DataTableInclude | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["job-id"] = job_id

    json_include: str | Unset = UNSET
    if not isinstance(include, Unset):
        json_include = include.value

    params["include"] = json_include

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v3/workspaces/{workspace_id}/projects/{project_id}/runs/{run_id}/run-results/{run_result_name}/tables/{result_table_name}",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | ResponseWrapper | TableDataResponse | None:
    if response.status_code == 200:
        response_200 = TableDataResponse.from_dict(response.json())

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

    if response.status_code == 410:
        response_410 = ResponseWrapper.from_dict(response.json())

        return response_410

    if response.status_code == 415:
        response_415 = cast(Any, None)
        return response_415

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | ResponseWrapper | TableDataResponse]:
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
    run_result_name: str,
    result_table_name: str,
    *,
    client: AuthenticatedClient | Client,
    job_id: int | Unset = UNSET,
    include: DataTableInclude | Unset = UNSET,
) -> Response[Any | ResponseWrapper | TableDataResponse]:
    """Gets the data in a result table.

    Args:
        workspace_id (int):
        project_id (int):
        run_id (int):
        run_result_name (str):
        result_table_name (str):
        job_id (int | Unset):
        include (DataTableInclude | Unset): Used in a GetDataTableForRun query to indicate whether
            you are interested in the table definition, the table data or both of these things.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ResponseWrapper | TableDataResponse]
    """

    kwargs = _get_kwargs(
        workspace_id=workspace_id,
        project_id=project_id,
        run_id=run_id,
        run_result_name=run_result_name,
        result_table_name=result_table_name,
        job_id=job_id,
        include=include,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    workspace_id: int,
    project_id: int,
    run_id: int,
    run_result_name: str,
    result_table_name: str,
    *,
    client: AuthenticatedClient | Client,
    job_id: int | Unset = UNSET,
    include: DataTableInclude | Unset = UNSET,
) -> Any | ResponseWrapper | TableDataResponse | None:
    """Gets the data in a result table.

    Args:
        workspace_id (int):
        project_id (int):
        run_id (int):
        run_result_name (str):
        result_table_name (str):
        job_id (int | Unset):
        include (DataTableInclude | Unset): Used in a GetDataTableForRun query to indicate whether
            you are interested in the table definition, the table data or both of these things.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ResponseWrapper | TableDataResponse
    """

    return sync_detailed(
        workspace_id=workspace_id,
        project_id=project_id,
        run_id=run_id,
        run_result_name=run_result_name,
        result_table_name=result_table_name,
        client=client,
        job_id=job_id,
        include=include,
    ).parsed


async def asyncio_detailed(
    workspace_id: int,
    project_id: int,
    run_id: int,
    run_result_name: str,
    result_table_name: str,
    *,
    client: AuthenticatedClient | Client,
    job_id: int | Unset = UNSET,
    include: DataTableInclude | Unset = UNSET,
) -> Response[Any | ResponseWrapper | TableDataResponse]:
    """Gets the data in a result table.

    Args:
        workspace_id (int):
        project_id (int):
        run_id (int):
        run_result_name (str):
        result_table_name (str):
        job_id (int | Unset):
        include (DataTableInclude | Unset): Used in a GetDataTableForRun query to indicate whether
            you are interested in the table definition, the table data or both of these things.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ResponseWrapper | TableDataResponse]
    """

    kwargs = _get_kwargs(
        workspace_id=workspace_id,
        project_id=project_id,
        run_id=run_id,
        run_result_name=run_result_name,
        result_table_name=result_table_name,
        job_id=job_id,
        include=include,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace_id: int,
    project_id: int,
    run_id: int,
    run_result_name: str,
    result_table_name: str,
    *,
    client: AuthenticatedClient | Client,
    job_id: int | Unset = UNSET,
    include: DataTableInclude | Unset = UNSET,
) -> Any | ResponseWrapper | TableDataResponse | None:
    """Gets the data in a result table.

    Args:
        workspace_id (int):
        project_id (int):
        run_id (int):
        run_result_name (str):
        result_table_name (str):
        job_id (int | Unset):
        include (DataTableInclude | Unset): Used in a GetDataTableForRun query to indicate whether
            you are interested in the table definition, the table data or both of these things.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ResponseWrapper | TableDataResponse
    """

    return (
        await asyncio_detailed(
            workspace_id=workspace_id,
            project_id=project_id,
            run_id=run_id,
            run_result_name=run_result_name,
            result_table_name=result_table_name,
            client=client,
            job_id=job_id,
            include=include,
        )
    ).parsed
