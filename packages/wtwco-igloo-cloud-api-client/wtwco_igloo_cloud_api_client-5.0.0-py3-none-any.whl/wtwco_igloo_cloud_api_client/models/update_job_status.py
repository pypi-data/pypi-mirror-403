from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.job_state import JobState
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateJobStatus")


@_attrs_define
class UpdateJobStatus:
    """
    Attributes:
        status (JobState | Unset): The state of a Job. This can be one of the following values:
             * InProgress - The job is currently being calculated.
             * Completed - The job has finished calculating and the results are ready to be viewed.
             * Warned - The job has finished calculating and the results are ready to be viewed, however the model emitted a
            warning message.
             * Error - The job has finished calculating, however the model calculation terminated early due to an error.
    """

    status: JobState | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _status = d.pop("status", UNSET)
        status: JobState | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = JobState(_status)

        update_job_status = cls(
            status=status,
        )

        return update_job_status
