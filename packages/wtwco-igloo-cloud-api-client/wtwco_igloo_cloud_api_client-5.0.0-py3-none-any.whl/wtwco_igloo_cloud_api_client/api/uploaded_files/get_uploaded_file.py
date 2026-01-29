from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.response_wrapper import ResponseWrapper
from ...models.uploaded_file_response import UploadedFileResponse
from ...types import Response


def _get_kwargs(
    workspace_id: int,
    file_id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v3/workspaces/{workspace_id}/uploaded-files/{file_id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | ResponseWrapper | UploadedFileResponse | None:
    if response.status_code == 200:
        response_200 = UploadedFileResponse.from_dict(response.json())

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

    if response.status_code == 415:
        response_415 = cast(Any, None)
        return response_415

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | ResponseWrapper | UploadedFileResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    workspace_id: int,
    file_id: int,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | ResponseWrapper | UploadedFileResponse]:
    """Gets the name, description and other details of a file.

    Args:
        workspace_id (int):
        file_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ResponseWrapper | UploadedFileResponse]
    """

    kwargs = _get_kwargs(
        workspace_id=workspace_id,
        file_id=file_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    workspace_id: int,
    file_id: int,
    *,
    client: AuthenticatedClient | Client,
) -> Any | ResponseWrapper | UploadedFileResponse | None:
    """Gets the name, description and other details of a file.

    Args:
        workspace_id (int):
        file_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ResponseWrapper | UploadedFileResponse
    """

    return sync_detailed(
        workspace_id=workspace_id,
        file_id=file_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    workspace_id: int,
    file_id: int,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | ResponseWrapper | UploadedFileResponse]:
    """Gets the name, description and other details of a file.

    Args:
        workspace_id (int):
        file_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ResponseWrapper | UploadedFileResponse]
    """

    kwargs = _get_kwargs(
        workspace_id=workspace_id,
        file_id=file_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace_id: int,
    file_id: int,
    *,
    client: AuthenticatedClient | Client,
) -> Any | ResponseWrapper | UploadedFileResponse | None:
    """Gets the name, description and other details of a file.

    Args:
        workspace_id (int):
        file_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ResponseWrapper | UploadedFileResponse
    """

    return (
        await asyncio_detailed(
            workspace_id=workspace_id,
            file_id=file_id,
            client=client,
        )
    ).parsed
