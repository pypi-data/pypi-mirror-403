from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_project import CreateProject
from ...models.project_response import ProjectResponse
from ...models.response_wrapper import ResponseWrapper
from ...types import Response


def _get_kwargs(
    workspace_id: int,
    *,
    body: CreateProject,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v3/workspaces/{workspace_id}/projects",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | ProjectResponse | ResponseWrapper | None:
    if response.status_code == 201:
        response_201 = ProjectResponse.from_dict(response.json())

        return response_201

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
) -> Response[Any | ProjectResponse | ResponseWrapper]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    workspace_id: int,
    *,
    client: AuthenticatedClient | Client,
    body: CreateProject,
) -> Response[Any | ProjectResponse | ResponseWrapper]:
    """Create a new project which uses the specified model version.

    Args:
        workspace_id (int):
        body (CreateProject):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ProjectResponse | ResponseWrapper]
    """

    kwargs = _get_kwargs(
        workspace_id=workspace_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    workspace_id: int,
    *,
    client: AuthenticatedClient | Client,
    body: CreateProject,
) -> Any | ProjectResponse | ResponseWrapper | None:
    """Create a new project which uses the specified model version.

    Args:
        workspace_id (int):
        body (CreateProject):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ProjectResponse | ResponseWrapper
    """

    return sync_detailed(
        workspace_id=workspace_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    workspace_id: int,
    *,
    client: AuthenticatedClient | Client,
    body: CreateProject,
) -> Response[Any | ProjectResponse | ResponseWrapper]:
    """Create a new project which uses the specified model version.

    Args:
        workspace_id (int):
        body (CreateProject):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ProjectResponse | ResponseWrapper]
    """

    kwargs = _get_kwargs(
        workspace_id=workspace_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace_id: int,
    *,
    client: AuthenticatedClient | Client,
    body: CreateProject,
) -> Any | ProjectResponse | ResponseWrapper | None:
    """Create a new project which uses the specified model version.

    Args:
        workspace_id (int):
        body (CreateProject):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ProjectResponse | ResponseWrapper
    """

    return (
        await asyncio_detailed(
            workspace_id=workspace_id,
            client=client,
            body=body,
        )
    ).parsed
