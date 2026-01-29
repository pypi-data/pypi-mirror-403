from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_o_data_for_run_response_200 import GetODataForRunResponse200
from ...types import UNSET, Response, Unset


def _get_kwargs(
    workspace_id: int,
    project_id: int,
    run_id: int,
    table_name: str,
    *,
    filter_: str | Unset = UNSET,
    select: str | Unset = UNSET,
    orderby: str | Unset = UNSET,
    top: int | Unset = UNSET,
    skip: int | Unset = UNSET,
    count: bool | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["$filter"] = filter_

    params["$select"] = select

    params["$orderby"] = orderby

    params["$top"] = top

    params["$skip"] = skip

    params["$count"] = count

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v3/workspaces/{workspace_id}/projects/{project_id}/runs/{run_id}/odata/{table_name}",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | GetODataForRunResponse200 | None:
    if response.status_code == 200:
        response_200 = GetODataForRunResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = cast(Any, None)
        return response_400

    if response.status_code == 401:
        response_401 = cast(Any, None)
        return response_401

    if response.status_code == 404:
        response_404 = cast(Any, None)
        return response_404

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | GetODataForRunResponse200]:
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
    table_name: str,
    *,
    client: AuthenticatedClient | Client,
    filter_: str | Unset = UNSET,
    select: str | Unset = UNSET,
    orderby: str | Unset = UNSET,
    top: int | Unset = UNSET,
    skip: int | Unset = UNSET,
    count: bool | Unset = UNSET,
) -> Response[Any | GetODataForRunResponse200]:
    """Get the data for a table in a run

     This endpoint allows you to get the data for a table in a run including result data. This is an
    OData call so operations to filter/sort/etc. the data are supported

    Args:
        workspace_id (int):
        project_id (int):
        run_id (int):
        table_name (str):
        filter_ (str | Unset):
        select (str | Unset):
        orderby (str | Unset):
        top (int | Unset):
        skip (int | Unset):
        count (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | GetODataForRunResponse200]
    """

    kwargs = _get_kwargs(
        workspace_id=workspace_id,
        project_id=project_id,
        run_id=run_id,
        table_name=table_name,
        filter_=filter_,
        select=select,
        orderby=orderby,
        top=top,
        skip=skip,
        count=count,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    workspace_id: int,
    project_id: int,
    run_id: int,
    table_name: str,
    *,
    client: AuthenticatedClient | Client,
    filter_: str | Unset = UNSET,
    select: str | Unset = UNSET,
    orderby: str | Unset = UNSET,
    top: int | Unset = UNSET,
    skip: int | Unset = UNSET,
    count: bool | Unset = UNSET,
) -> Any | GetODataForRunResponse200 | None:
    """Get the data for a table in a run

     This endpoint allows you to get the data for a table in a run including result data. This is an
    OData call so operations to filter/sort/etc. the data are supported

    Args:
        workspace_id (int):
        project_id (int):
        run_id (int):
        table_name (str):
        filter_ (str | Unset):
        select (str | Unset):
        orderby (str | Unset):
        top (int | Unset):
        skip (int | Unset):
        count (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | GetODataForRunResponse200
    """

    return sync_detailed(
        workspace_id=workspace_id,
        project_id=project_id,
        run_id=run_id,
        table_name=table_name,
        client=client,
        filter_=filter_,
        select=select,
        orderby=orderby,
        top=top,
        skip=skip,
        count=count,
    ).parsed


async def asyncio_detailed(
    workspace_id: int,
    project_id: int,
    run_id: int,
    table_name: str,
    *,
    client: AuthenticatedClient | Client,
    filter_: str | Unset = UNSET,
    select: str | Unset = UNSET,
    orderby: str | Unset = UNSET,
    top: int | Unset = UNSET,
    skip: int | Unset = UNSET,
    count: bool | Unset = UNSET,
) -> Response[Any | GetODataForRunResponse200]:
    """Get the data for a table in a run

     This endpoint allows you to get the data for a table in a run including result data. This is an
    OData call so operations to filter/sort/etc. the data are supported

    Args:
        workspace_id (int):
        project_id (int):
        run_id (int):
        table_name (str):
        filter_ (str | Unset):
        select (str | Unset):
        orderby (str | Unset):
        top (int | Unset):
        skip (int | Unset):
        count (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | GetODataForRunResponse200]
    """

    kwargs = _get_kwargs(
        workspace_id=workspace_id,
        project_id=project_id,
        run_id=run_id,
        table_name=table_name,
        filter_=filter_,
        select=select,
        orderby=orderby,
        top=top,
        skip=skip,
        count=count,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace_id: int,
    project_id: int,
    run_id: int,
    table_name: str,
    *,
    client: AuthenticatedClient | Client,
    filter_: str | Unset = UNSET,
    select: str | Unset = UNSET,
    orderby: str | Unset = UNSET,
    top: int | Unset = UNSET,
    skip: int | Unset = UNSET,
    count: bool | Unset = UNSET,
) -> Any | GetODataForRunResponse200 | None:
    """Get the data for a table in a run

     This endpoint allows you to get the data for a table in a run including result data. This is an
    OData call so operations to filter/sort/etc. the data are supported

    Args:
        workspace_id (int):
        project_id (int):
        run_id (int):
        table_name (str):
        filter_ (str | Unset):
        select (str | Unset):
        orderby (str | Unset):
        top (int | Unset):
        skip (int | Unset):
        count (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | GetODataForRunResponse200
    """

    return (
        await asyncio_detailed(
            workspace_id=workspace_id,
            project_id=project_id,
            run_id=run_id,
            table_name=table_name,
            client=client,
            filter_=filter_,
            select=select,
            orderby=orderby,
            top=top,
            skip=skip,
            count=count,
        )
    ).parsed
