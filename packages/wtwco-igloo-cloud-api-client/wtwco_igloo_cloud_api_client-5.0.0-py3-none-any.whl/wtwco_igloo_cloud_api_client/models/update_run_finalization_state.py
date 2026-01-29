from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.run_finalization_state import RunFinalizationState
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateRunFinalizationState")


@_attrs_define
class UpdateRunFinalizationState:
    """
    Attributes:
        state (RunFinalizationState | Unset): The finalization state of a Run. This can be one of the following values:
             * NotFinalized - The run has not been finalized yet.
             * FinalizationRequested - This value is used to post to the UpdateRunFinalizationState endpoint when finalizing
            run.
             * Finalizing - The run is the process of being finalized.
             * Finalized - The run has been finalized and can no longer be modified or recalculated.
    """

    state: RunFinalizationState | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        state: str | Unset = UNSET
        if not isinstance(self.state, Unset):
            state = self.state.value

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if state is not UNSET:
            field_dict["state"] = state

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _state = d.pop("state", UNSET)
        state: RunFinalizationState | Unset
        if isinstance(_state, Unset):
            state = UNSET
        else:
            state = RunFinalizationState(_state)

        update_run_finalization_state = cls(
            state=state,
        )

        return update_run_finalization_state
