from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.run_error_type import RunErrorType
from ..types import UNSET, Unset

T = TypeVar("T", bound="RunError")


@_attrs_define
class RunError:
    """Represents an error attached to a run.

    Attributes:
        type_ (RunErrorType | Unset): Indicates the reason for this error.
             * Unknown - The Run errored for an unknown reason.
             * Job -  An error occurred during the execution of the job that calculated this run.
             * TableCalculation - An error occurred calculating calculated tables for a run.
             * Finalization - An error occurred during the finalization of a run.
        message (None | str | Unset): A description of the error.
    """

    type_: RunErrorType | Unset = UNSET
    message: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        message: None | str | Unset
        if isinstance(self.message, Unset):
            message = UNSET
        else:
            message = self.message

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if type_ is not UNSET:
            field_dict["type"] = type_
        if message is not UNSET:
            field_dict["message"] = message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _type_ = d.pop("type", UNSET)
        type_: RunErrorType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = RunErrorType(_type_)

        def _parse_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        message = _parse_message(d.pop("message", UNSET))

        run_error = cls(
            type_=type_,
            message=message,
        )

        return run_error
