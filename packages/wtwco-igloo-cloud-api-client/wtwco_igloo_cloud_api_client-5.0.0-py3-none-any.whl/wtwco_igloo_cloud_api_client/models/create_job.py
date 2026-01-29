from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateJob")


@_attrs_define
class CreateJob:
    """
    Attributes:
        project_id (int): The id of the project that contains the run you wish to calculate.
        run_id (int): The id of the run that you wish to calculate.
        pool (None | str | Unset): The name of the pool you wish to use to calculate the model.
        pool_id (int | None | Unset): The id of the pool you wish to use to calculate the model. Use this instead of
            Pool to specify the pool by id.
    """

    project_id: int
    run_id: int
    pool: None | str | Unset = UNSET
    pool_id: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        project_id = self.project_id

        run_id = self.run_id

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

        field_dict.update(
            {
                "projectId": project_id,
                "runId": run_id,
            }
        )
        if pool is not UNSET:
            field_dict["pool"] = pool
        if pool_id is not UNSET:
            field_dict["poolId"] = pool_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        project_id = d.pop("projectId")

        run_id = d.pop("runId")

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

        create_job = cls(
            project_id=project_id,
            run_id=run_id,
            pool=pool,
            pool_id=pool_id,
        )

        return create_job
