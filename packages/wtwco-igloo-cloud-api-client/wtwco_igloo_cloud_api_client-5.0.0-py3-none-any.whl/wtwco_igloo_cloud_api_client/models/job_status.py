from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.job_state import JobState
from ..types import UNSET, Unset

T = TypeVar("T", bound="JobStatus")


@_attrs_define
class JobStatus:
    """
    Attributes:
        error_message (None | str | Unset): If non-null then provides a warning or error message that was raised by
            Igloo Cloud when the run was calculated.
        status_message (None | str | Unset): If non-null then provides a message about what this job is doing now.
        link (None | str | Unset): Provides a Url to use to view the job on Igloo Cloud.
        state (JobState | Unset): The state of a Job. This can be one of the following values:
             * InProgress - The job is currently being calculated.
             * Completed - The job has finished calculating and the results are ready to be viewed.
             * Warned - The job has finished calculating and the results are ready to be viewed, however the model emitted a
            warning message.
             * Error - The job has finished calculating, however the model calculation terminated early due to an error.
    """

    error_message: None | str | Unset = UNSET
    status_message: None | str | Unset = UNSET
    link: None | str | Unset = UNSET
    state: JobState | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        error_message: None | str | Unset
        if isinstance(self.error_message, Unset):
            error_message = UNSET
        else:
            error_message = self.error_message

        status_message: None | str | Unset
        if isinstance(self.status_message, Unset):
            status_message = UNSET
        else:
            status_message = self.status_message

        link: None | str | Unset
        if isinstance(self.link, Unset):
            link = UNSET
        else:
            link = self.link

        state: str | Unset = UNSET
        if not isinstance(self.state, Unset):
            state = self.state.value

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if error_message is not UNSET:
            field_dict["errorMessage"] = error_message
        if status_message is not UNSET:
            field_dict["statusMessage"] = status_message
        if link is not UNSET:
            field_dict["link"] = link
        if state is not UNSET:
            field_dict["state"] = state

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_error_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error_message = _parse_error_message(d.pop("errorMessage", UNSET))

        def _parse_status_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        status_message = _parse_status_message(d.pop("statusMessage", UNSET))

        def _parse_link(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        link = _parse_link(d.pop("link", UNSET))

        _state = d.pop("state", UNSET)
        state: JobState | Unset
        if isinstance(_state, Unset):
            state = UNSET
        else:
            state = JobState(_state)

        job_status = cls(
            error_message=error_message,
            status_message=status_message,
            link=link,
            state=state,
        )

        return job_status
