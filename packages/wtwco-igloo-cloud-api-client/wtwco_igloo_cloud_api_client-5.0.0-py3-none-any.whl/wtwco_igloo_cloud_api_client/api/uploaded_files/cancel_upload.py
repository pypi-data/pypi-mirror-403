from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.response_wrapper import ResponseWrapper
from ...types import Response


def _get_kwargs(
    workspace_id: int,
    file_id: int,
    upload_identifier: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": f"/api/v3/workspaces/{workspace_id}/uploaded-files/{file_id}/upload/{upload_identifier}",
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | ResponseWrapper | None:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

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
) -> Response[Any | ResponseWrapper]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    workspace_id: int,
    file_id: int,
    upload_identifier: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | ResponseWrapper]:
    """Cancel the file uploading process. This should only be called if the file is currently in the
    Uploading state.

    Args:
        workspace_id (int):
        file_id (int):
        upload_identifier (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ResponseWrapper]
    """

    kwargs = _get_kwargs(
        workspace_id=workspace_id,
        file_id=file_id,
        upload_identifier=upload_identifier,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    workspace_id: int,
    file_id: int,
    upload_identifier: str,
    *,
    client: AuthenticatedClient | Client,
) -> Any | ResponseWrapper | None:
    """Cancel the file uploading process. This should only be called if the file is currently in the
    Uploading state.

    Args:
        workspace_id (int):
        file_id (int):
        upload_identifier (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ResponseWrapper
    """

    return sync_detailed(
        workspace_id=workspace_id,
        file_id=file_id,
        upload_identifier=upload_identifier,
        client=client,
    ).parsed


async def asyncio_detailed(
    workspace_id: int,
    file_id: int,
    upload_identifier: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | ResponseWrapper]:
    """Cancel the file uploading process. This should only be called if the file is currently in the
    Uploading state.

    Args:
        workspace_id (int):
        file_id (int):
        upload_identifier (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ResponseWrapper]
    """

    kwargs = _get_kwargs(
        workspace_id=workspace_id,
        file_id=file_id,
        upload_identifier=upload_identifier,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace_id: int,
    file_id: int,
    upload_identifier: str,
    *,
    client: AuthenticatedClient | Client,
) -> Any | ResponseWrapper | None:
    """Cancel the file uploading process. This should only be called if the file is currently in the
    Uploading state.

    Args:
        workspace_id (int):
        file_id (int):
        upload_identifier (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ResponseWrapper
    """

    return (
        await asyncio_detailed(
            workspace_id=workspace_id,
            file_id=file_id,
            upload_identifier=upload_identifier,
            client=client,
        )
    ).parsed
