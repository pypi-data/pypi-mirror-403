from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.run_finalization_state import RunFinalizationState
from ..models.run_state import RunState
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.owned_data_group import OwnedDataGroup
    from ..models.run_error import RunError


T = TypeVar("T", bound="Run")


@_attrs_define
class Run:
    """
    Attributes:
        id (int | Unset): The id value of this run.
        project_id (int | Unset): The id of the project.
        workspace_id (int | Unset): The id of the workspace.
        name (None | str | Unset): The name for this run.
        parent_id (int | None | Unset): The id of our parent run, or null if we are the base run in the project.
        description (None | str | Unset): The description of this run.
        auto_deletion_time (datetime.datetime | None | Unset): If this value is non-null then it specified the date and
            time after which the run may be automatically deleted.
        state (RunState | Unset): The state of a Run. This can be one of the following values:
             * Processing - The input data is not ready to be viewed, this may be because the run is being initialised or
            some processing is happening as the result of a recent input data change.
             * Uncalculated - The run has not been calculated since the input data was last modified.
             * InProgress - The run is currently being calculated.
             * Completed - The run has been calculated for the latest input data changes and the results are ready to be
            viewed.
             * Warned - The run has been calculated for the latest input data changes and the results are ready to be
            viewed, however the model emitted a warning message.
             * Error - The run failed to calculate with the latest input data changes.
        finalization_state (RunFinalizationState | Unset): The finalization state of a Run. This can be one of the
            following values:
             * NotFinalized - The run has not been finalized yet.
             * FinalizationRequested - This value is used to post to the UpdateRunFinalizationState endpoint when finalizing
            run.
             * Finalizing - The run is the process of being finalized.
             * Finalized - The run has been finalized and can no longer be modified or recalculated.
        owned_data_groups (list[OwnedDataGroup] | None | Unset): A list of data groups whose data has been modified by
            this run.
        job_id (int | None | Unset): The Job id of the job that calculated this run, or null if the run is not
            calculated or being calculated.
        job_link (None | str | Unset): If non-null then provides a Url to use to view the job on Igloo Cloud which
            calculated this run.
        job_error (None | str | Unset): If non-null then provides a warning or error message that was raised by Igloo
            Cloud when the run was calculated.
        job_status_message (None | str | Unset): If non-null then provides a message about what this job is doing now.
        errors (list[RunError] | None | Unset): The error message for this run, if any, including any error from the
            job.
    """

    id: int | Unset = UNSET
    project_id: int | Unset = UNSET
    workspace_id: int | Unset = UNSET
    name: None | str | Unset = UNSET
    parent_id: int | None | Unset = UNSET
    description: None | str | Unset = UNSET
    auto_deletion_time: datetime.datetime | None | Unset = UNSET
    state: RunState | Unset = UNSET
    finalization_state: RunFinalizationState | Unset = UNSET
    owned_data_groups: list[OwnedDataGroup] | None | Unset = UNSET
    job_id: int | None | Unset = UNSET
    job_link: None | str | Unset = UNSET
    job_error: None | str | Unset = UNSET
    job_status_message: None | str | Unset = UNSET
    errors: list[RunError] | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        project_id = self.project_id

        workspace_id = self.workspace_id

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        parent_id: int | None | Unset
        if isinstance(self.parent_id, Unset):
            parent_id = UNSET
        else:
            parent_id = self.parent_id

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        auto_deletion_time: None | str | Unset
        if isinstance(self.auto_deletion_time, Unset):
            auto_deletion_time = UNSET
        elif isinstance(self.auto_deletion_time, datetime.datetime):
            auto_deletion_time = self.auto_deletion_time.isoformat()
        else:
            auto_deletion_time = self.auto_deletion_time

        state: str | Unset = UNSET
        if not isinstance(self.state, Unset):
            state = self.state.value

        finalization_state: str | Unset = UNSET
        if not isinstance(self.finalization_state, Unset):
            finalization_state = self.finalization_state.value

        owned_data_groups: list[dict[str, Any]] | None | Unset
        if isinstance(self.owned_data_groups, Unset):
            owned_data_groups = UNSET
        elif isinstance(self.owned_data_groups, list):
            owned_data_groups = []
            for owned_data_groups_type_0_item_data in self.owned_data_groups:
                owned_data_groups_type_0_item = owned_data_groups_type_0_item_data.to_dict()
                owned_data_groups.append(owned_data_groups_type_0_item)

        else:
            owned_data_groups = self.owned_data_groups

        job_id: int | None | Unset
        if isinstance(self.job_id, Unset):
            job_id = UNSET
        else:
            job_id = self.job_id

        job_link: None | str | Unset
        if isinstance(self.job_link, Unset):
            job_link = UNSET
        else:
            job_link = self.job_link

        job_error: None | str | Unset
        if isinstance(self.job_error, Unset):
            job_error = UNSET
        else:
            job_error = self.job_error

        job_status_message: None | str | Unset
        if isinstance(self.job_status_message, Unset):
            job_status_message = UNSET
        else:
            job_status_message = self.job_status_message

        errors: list[dict[str, Any]] | None | Unset
        if isinstance(self.errors, Unset):
            errors = UNSET
        elif isinstance(self.errors, list):
            errors = []
            for errors_type_0_item_data in self.errors:
                errors_type_0_item = errors_type_0_item_data.to_dict()
                errors.append(errors_type_0_item)

        else:
            errors = self.errors

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if project_id is not UNSET:
            field_dict["projectId"] = project_id
        if workspace_id is not UNSET:
            field_dict["workspaceId"] = workspace_id
        if name is not UNSET:
            field_dict["name"] = name
        if parent_id is not UNSET:
            field_dict["parentId"] = parent_id
        if description is not UNSET:
            field_dict["description"] = description
        if auto_deletion_time is not UNSET:
            field_dict["autoDeletionTime"] = auto_deletion_time
        if state is not UNSET:
            field_dict["state"] = state
        if finalization_state is not UNSET:
            field_dict["finalizationState"] = finalization_state
        if owned_data_groups is not UNSET:
            field_dict["ownedDataGroups"] = owned_data_groups
        if job_id is not UNSET:
            field_dict["jobId"] = job_id
        if job_link is not UNSET:
            field_dict["jobLink"] = job_link
        if job_error is not UNSET:
            field_dict["jobError"] = job_error
        if job_status_message is not UNSET:
            field_dict["jobStatusMessage"] = job_status_message
        if errors is not UNSET:
            field_dict["errors"] = errors

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.owned_data_group import OwnedDataGroup
        from ..models.run_error import RunError

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        project_id = d.pop("projectId", UNSET)

        workspace_id = d.pop("workspaceId", UNSET)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_parent_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        parent_id = _parse_parent_id(d.pop("parentId", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_auto_deletion_time(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                auto_deletion_time_type_0 = isoparse(data)

                return auto_deletion_time_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        auto_deletion_time = _parse_auto_deletion_time(d.pop("autoDeletionTime", UNSET))

        _state = d.pop("state", UNSET)
        state: RunState | Unset
        if isinstance(_state, Unset):
            state = UNSET
        else:
            state = RunState(_state)

        _finalization_state = d.pop("finalizationState", UNSET)
        finalization_state: RunFinalizationState | Unset
        if isinstance(_finalization_state, Unset):
            finalization_state = UNSET
        else:
            finalization_state = RunFinalizationState(_finalization_state)

        def _parse_owned_data_groups(data: object) -> list[OwnedDataGroup] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                owned_data_groups_type_0 = []
                _owned_data_groups_type_0 = data
                for owned_data_groups_type_0_item_data in _owned_data_groups_type_0:
                    owned_data_groups_type_0_item = OwnedDataGroup.from_dict(owned_data_groups_type_0_item_data)

                    owned_data_groups_type_0.append(owned_data_groups_type_0_item)

                return owned_data_groups_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[OwnedDataGroup] | None | Unset, data)

        owned_data_groups = _parse_owned_data_groups(d.pop("ownedDataGroups", UNSET))

        def _parse_job_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        job_id = _parse_job_id(d.pop("jobId", UNSET))

        def _parse_job_link(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        job_link = _parse_job_link(d.pop("jobLink", UNSET))

        def _parse_job_error(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        job_error = _parse_job_error(d.pop("jobError", UNSET))

        def _parse_job_status_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        job_status_message = _parse_job_status_message(d.pop("jobStatusMessage", UNSET))

        def _parse_errors(data: object) -> list[RunError] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                errors_type_0 = []
                _errors_type_0 = data
                for errors_type_0_item_data in _errors_type_0:
                    errors_type_0_item = RunError.from_dict(errors_type_0_item_data)

                    errors_type_0.append(errors_type_0_item)

                return errors_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[RunError] | None | Unset, data)

        errors = _parse_errors(d.pop("errors", UNSET))

        run = cls(
            id=id,
            project_id=project_id,
            workspace_id=workspace_id,
            name=name,
            parent_id=parent_id,
            description=description,
            auto_deletion_time=auto_deletion_time,
            state=state,
            finalization_state=finalization_state,
            owned_data_groups=owned_data_groups,
            job_id=job_id,
            job_link=job_link,
            job_error=job_error,
            job_status_message=job_status_message,
            errors=errors,
        )

        return run
