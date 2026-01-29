from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.response_wrapper import ResponseWrapper
from ...models.upload_progress import UploadProgress
from ...types import Response


def _get_kwargs(
    workspace_id: int,
    file_id: int,
    upload_identifier: str,
    *,
    body: UploadProgress,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/api/v3/workspaces/{workspace_id}/uploaded-files/{file_id}/upload/{upload_identifier}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | ResponseWrapper | None:
    if response.status_code == 200:
        response_200 = cast(Any, None)
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
    body: UploadProgress,
) -> Response[Any | ResponseWrapper]:
    """Update the file upload progress information. You must call this endpoint with UploadPercent equal to
    100
    to indicate that the file upload process has completed.
    When this has been done the status of the file will change to UploadCompleting while the system
    scans the contents, followed by Uploaded
    a short time later.

    Args:
        workspace_id (int):
        file_id (int):
        upload_identifier (str):
        body (UploadProgress):

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
        body=body,
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
    body: UploadProgress,
) -> Any | ResponseWrapper | None:
    """Update the file upload progress information. You must call this endpoint with UploadPercent equal to
    100
    to indicate that the file upload process has completed.
    When this has been done the status of the file will change to UploadCompleting while the system
    scans the contents, followed by Uploaded
    a short time later.

    Args:
        workspace_id (int):
        file_id (int):
        upload_identifier (str):
        body (UploadProgress):

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
        body=body,
    ).parsed


async def asyncio_detailed(
    workspace_id: int,
    file_id: int,
    upload_identifier: str,
    *,
    client: AuthenticatedClient | Client,
    body: UploadProgress,
) -> Response[Any | ResponseWrapper]:
    """Update the file upload progress information. You must call this endpoint with UploadPercent equal to
    100
    to indicate that the file upload process has completed.
    When this has been done the status of the file will change to UploadCompleting while the system
    scans the contents, followed by Uploaded
    a short time later.

    Args:
        workspace_id (int):
        file_id (int):
        upload_identifier (str):
        body (UploadProgress):

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
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace_id: int,
    file_id: int,
    upload_identifier: str,
    *,
    client: AuthenticatedClient | Client,
    body: UploadProgress,
) -> Any | ResponseWrapper | None:
    """Update the file upload progress information. You must call this endpoint with UploadPercent equal to
    100
    to indicate that the file upload process has completed.
    When this has been done the status of the file will change to UploadCompleting while the system
    scans the contents, followed by Uploaded
    a short time later.

    Args:
        workspace_id (int):
        file_id (int):
        upload_identifier (str):
        body (UploadProgress):

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
            body=body,
        )
    ).parsed
