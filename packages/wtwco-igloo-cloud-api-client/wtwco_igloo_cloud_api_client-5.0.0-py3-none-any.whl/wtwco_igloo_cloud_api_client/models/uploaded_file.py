from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="UploadedFile")


@_attrs_define
class UploadedFile:
    """
    Attributes:
        id (int | Unset): The id value of this uploaded file.
        workspace_id (int | Unset): The id of the workspace containing this file.
        name (None | str | Unset): The name of this uploaded file.
        extension (None | str | Unset): The file extension of the uploaded file.
        description (None | str | Unset): The description of the uploaded file.
        upload_status (None | str | Unset): Indicates the upload status of this file. One of UploadNotStarted,
            Uploading, UploadCompleting, Uploaded or UploadFailedOrCancelled.
        uploaded_by (None | str | Unset): The name of the user who uploaded the content of this file.
        upload_start_time (datetime.datetime | None | Unset): The date and time when the file upload process was
            initiated.
        upload_percent (int | Unset): How much of the content has been uploaded to Azure blob storage.
        size_in_bytes (int | None | Unset): The total size of the file content.
        run_count (int | Unset): The number of runs whose input data reference this file.
        file_upload_identifier (None | str | Unset): The upload identifier to use in calls to UpdateProgress or
            CancelUpload.
    """

    id: int | Unset = UNSET
    workspace_id: int | Unset = UNSET
    name: None | str | Unset = UNSET
    extension: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    upload_status: None | str | Unset = UNSET
    uploaded_by: None | str | Unset = UNSET
    upload_start_time: datetime.datetime | None | Unset = UNSET
    upload_percent: int | Unset = UNSET
    size_in_bytes: int | None | Unset = UNSET
    run_count: int | Unset = UNSET
    file_upload_identifier: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        workspace_id = self.workspace_id

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        extension: None | str | Unset
        if isinstance(self.extension, Unset):
            extension = UNSET
        else:
            extension = self.extension

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        upload_status: None | str | Unset
        if isinstance(self.upload_status, Unset):
            upload_status = UNSET
        else:
            upload_status = self.upload_status

        uploaded_by: None | str | Unset
        if isinstance(self.uploaded_by, Unset):
            uploaded_by = UNSET
        else:
            uploaded_by = self.uploaded_by

        upload_start_time: None | str | Unset
        if isinstance(self.upload_start_time, Unset):
            upload_start_time = UNSET
        elif isinstance(self.upload_start_time, datetime.datetime):
            upload_start_time = self.upload_start_time.isoformat()
        else:
            upload_start_time = self.upload_start_time

        upload_percent = self.upload_percent

        size_in_bytes: int | None | Unset
        if isinstance(self.size_in_bytes, Unset):
            size_in_bytes = UNSET
        else:
            size_in_bytes = self.size_in_bytes

        run_count = self.run_count

        file_upload_identifier: None | str | Unset
        if isinstance(self.file_upload_identifier, Unset):
            file_upload_identifier = UNSET
        else:
            file_upload_identifier = self.file_upload_identifier

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if workspace_id is not UNSET:
            field_dict["workspaceId"] = workspace_id
        if name is not UNSET:
            field_dict["name"] = name
        if extension is not UNSET:
            field_dict["extension"] = extension
        if description is not UNSET:
            field_dict["description"] = description
        if upload_status is not UNSET:
            field_dict["uploadStatus"] = upload_status
        if uploaded_by is not UNSET:
            field_dict["uploadedBy"] = uploaded_by
        if upload_start_time is not UNSET:
            field_dict["uploadStartTime"] = upload_start_time
        if upload_percent is not UNSET:
            field_dict["uploadPercent"] = upload_percent
        if size_in_bytes is not UNSET:
            field_dict["sizeInBytes"] = size_in_bytes
        if run_count is not UNSET:
            field_dict["runCount"] = run_count
        if file_upload_identifier is not UNSET:
            field_dict["fileUploadIdentifier"] = file_upload_identifier

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        workspace_id = d.pop("workspaceId", UNSET)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_extension(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        extension = _parse_extension(d.pop("extension", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_upload_status(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        upload_status = _parse_upload_status(d.pop("uploadStatus", UNSET))

        def _parse_uploaded_by(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        uploaded_by = _parse_uploaded_by(d.pop("uploadedBy", UNSET))

        def _parse_upload_start_time(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                upload_start_time_type_0 = isoparse(data)

                return upload_start_time_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        upload_start_time = _parse_upload_start_time(d.pop("uploadStartTime", UNSET))

        upload_percent = d.pop("uploadPercent", UNSET)

        def _parse_size_in_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        size_in_bytes = _parse_size_in_bytes(d.pop("sizeInBytes", UNSET))

        run_count = d.pop("runCount", UNSET)

        def _parse_file_upload_identifier(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        file_upload_identifier = _parse_file_upload_identifier(d.pop("fileUploadIdentifier", UNSET))

        uploaded_file = cls(
            id=id,
            workspace_id=workspace_id,
            name=name,
            extension=extension,
            description=description,
            upload_status=upload_status,
            uploaded_by=uploaded_by,
            upload_start_time=upload_start_time,
            upload_percent=upload_percent,
            size_in_bytes=size_in_bytes,
            run_count=run_count,
            file_upload_identifier=file_upload_identifier,
        )

        return uploaded_file
