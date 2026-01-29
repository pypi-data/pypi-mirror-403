from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeleteRunResult")


@_attrs_define
class DeleteRunResult:
    """
    Attributes:
        deleted_run_ids (list[int] | None | Unset): The list of run ids that were deleted by the request.
    """

    deleted_run_ids: list[int] | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        deleted_run_ids: list[int] | None | Unset
        if isinstance(self.deleted_run_ids, Unset):
            deleted_run_ids = UNSET
        elif isinstance(self.deleted_run_ids, list):
            deleted_run_ids = self.deleted_run_ids

        else:
            deleted_run_ids = self.deleted_run_ids

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if deleted_run_ids is not UNSET:
            field_dict["deletedRunIds"] = deleted_run_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_deleted_run_ids(data: object) -> list[int] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                deleted_run_ids_type_0 = cast(list[int], data)

                return deleted_run_ids_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[int] | None | Unset, data)

        deleted_run_ids = _parse_deleted_run_ids(d.pop("deletedRunIds", UNSET))

        delete_run_result = cls(
            deleted_run_ids=deleted_run_ids,
        )

        return delete_run_result
