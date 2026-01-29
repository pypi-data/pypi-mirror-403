from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.id_and_name import IdAndName
    from ..models.job_status import JobStatus


T = TypeVar("T", bound="Job")


@_attrs_define
class Job:
    """
    Attributes:
        id (int | Unset): The id value of this job.
        workspace_id (int | Unset): The id of the workspace.
        project (IdAndName | Unset):
        run (IdAndName | Unset):
        status (JobStatus | Unset):
        start_time (datetime.datetime | None | Unset): The date and time when this job was submitted.
        finish_time (datetime.datetime | None | Unset): If non-null, supplies the date and time this job finished.
        user_name (None | str | Unset): The name of the user that submitted the job.
        pool (None | str | Unset): The name of the pool used to calculate the job.
        pool_id (int | None | Unset): The id of the pool used to calculate the job.
    """

    id: int | Unset = UNSET
    workspace_id: int | Unset = UNSET
    project: IdAndName | Unset = UNSET
    run: IdAndName | Unset = UNSET
    status: JobStatus | Unset = UNSET
    start_time: datetime.datetime | None | Unset = UNSET
    finish_time: datetime.datetime | None | Unset = UNSET
    user_name: None | str | Unset = UNSET
    pool: None | str | Unset = UNSET
    pool_id: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        workspace_id = self.workspace_id

        project: dict[str, Any] | Unset = UNSET
        if not isinstance(self.project, Unset):
            project = self.project.to_dict()

        run: dict[str, Any] | Unset = UNSET
        if not isinstance(self.run, Unset):
            run = self.run.to_dict()

        status: dict[str, Any] | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.to_dict()

        start_time: None | str | Unset
        if isinstance(self.start_time, Unset):
            start_time = UNSET
        elif isinstance(self.start_time, datetime.datetime):
            start_time = self.start_time.isoformat()
        else:
            start_time = self.start_time

        finish_time: None | str | Unset
        if isinstance(self.finish_time, Unset):
            finish_time = UNSET
        elif isinstance(self.finish_time, datetime.datetime):
            finish_time = self.finish_time.isoformat()
        else:
            finish_time = self.finish_time

        user_name: None | str | Unset
        if isinstance(self.user_name, Unset):
            user_name = UNSET
        else:
            user_name = self.user_name

        pool: None | str | Unset
        if isinstance(self.pool, Unset):
            pool = UNSET
        else:
            pool = self.pool

        pool_id: int | None | Unset
        if isinstance(self.pool_id, Unset):
            pool_id = UNSET
        else:
            pool_id = self.pool_id

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if workspace_id is not UNSET:
            field_dict["workspaceId"] = workspace_id
        if project is not UNSET:
            field_dict["project"] = project
        if run is not UNSET:
            field_dict["run"] = run
        if status is not UNSET:
            field_dict["status"] = status
        if start_time is not UNSET:
            field_dict["startTime"] = start_time
        if finish_time is not UNSET:
            field_dict["finishTime"] = finish_time
        if user_name is not UNSET:
            field_dict["userName"] = user_name
        if pool is not UNSET:
            field_dict["pool"] = pool
        if pool_id is not UNSET:
            field_dict["poolId"] = pool_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.id_and_name import IdAndName
        from ..models.job_status import JobStatus

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        workspace_id = d.pop("workspaceId", UNSET)

        _project = d.pop("project", UNSET)
        project: IdAndName | Unset
        if isinstance(_project, Unset):
            project = UNSET
        else:
            project = IdAndName.from_dict(_project)

        _run = d.pop("run", UNSET)
        run: IdAndName | Unset
        if isinstance(_run, Unset):
            run = UNSET
        else:
            run = IdAndName.from_dict(_run)

        _status = d.pop("status", UNSET)
        status: JobStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = JobStatus.from_dict(_status)

        def _parse_start_time(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                start_time_type_0 = isoparse(data)

                return start_time_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        start_time = _parse_start_time(d.pop("startTime", UNSET))

        def _parse_finish_time(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                finish_time_type_0 = isoparse(data)

                return finish_time_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        finish_time = _parse_finish_time(d.pop("finishTime", UNSET))

        def _parse_user_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        user_name = _parse_user_name(d.pop("userName", UNSET))

        def _parse_pool(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        pool = _parse_pool(d.pop("pool", UNSET))

        def _parse_pool_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        pool_id = _parse_pool_id(d.pop("poolId", UNSET))

        job = cls(
            id=id,
            workspace_id=workspace_id,
            project=project,
            run=run,
            status=status,
            start_time=start_time,
            finish_time=finish_time,
            user_name=user_name,
            pool=pool,
            pool_id=pool_id,
        )

        return job
