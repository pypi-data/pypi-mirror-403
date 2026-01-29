from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="Project")


@_attrs_define
class Project:
    """
    Attributes:
        id (int | Unset): The id value of this project.
        workspace_id (int | Unset): The id of the workspace containing this project.
        base_run_id (int | Unset): The id of the base run for this project.
        name (None | str | Unset): The name for this project.
        description (None | str | Unset): The description of the project.
        run_count (int | Unset): The number of runs of this project.
        model_version_id (int | Unset): The id of the model version used by the project.
        default_pool (None | str | Unset): The default pool for the project.
        default_pool_id (int | None | Unset): The default pool id for the project.
        contains_finalized_runs (bool | Unset): The project contains one or more finalized runs
    """

    id: int | Unset = UNSET
    workspace_id: int | Unset = UNSET
    base_run_id: int | Unset = UNSET
    name: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    run_count: int | Unset = UNSET
    model_version_id: int | Unset = UNSET
    default_pool: None | str | Unset = UNSET
    default_pool_id: int | None | Unset = UNSET
    contains_finalized_runs: bool | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        workspace_id = self.workspace_id

        base_run_id = self.base_run_id

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        run_count = self.run_count

        model_version_id = self.model_version_id

        default_pool: None | str | Unset
        if isinstance(self.default_pool, Unset):
            default_pool = UNSET
        else:
            default_pool = self.default_pool

        default_pool_id: int | None | Unset
        if isinstance(self.default_pool_id, Unset):
            default_pool_id = UNSET
        else:
            default_pool_id = self.default_pool_id

        contains_finalized_runs = self.contains_finalized_runs

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if workspace_id is not UNSET:
            field_dict["workspaceId"] = workspace_id
        if base_run_id is not UNSET:
            field_dict["baseRunId"] = base_run_id
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if run_count is not UNSET:
            field_dict["runCount"] = run_count
        if model_version_id is not UNSET:
            field_dict["modelVersionId"] = model_version_id
        if default_pool is not UNSET:
            field_dict["defaultPool"] = default_pool
        if default_pool_id is not UNSET:
            field_dict["defaultPoolId"] = default_pool_id
        if contains_finalized_runs is not UNSET:
            field_dict["containsFinalizedRuns"] = contains_finalized_runs

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        workspace_id = d.pop("workspaceId", UNSET)

        base_run_id = d.pop("baseRunId", UNSET)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        run_count = d.pop("runCount", UNSET)

        model_version_id = d.pop("modelVersionId", UNSET)

        def _parse_default_pool(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        default_pool = _parse_default_pool(d.pop("defaultPool", UNSET))

        def _parse_default_pool_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        default_pool_id = _parse_default_pool_id(d.pop("defaultPoolId", UNSET))

        contains_finalized_runs = d.pop("containsFinalizedRuns", UNSET)

        project = cls(
            id=id,
            workspace_id=workspace_id,
            base_run_id=base_run_id,
            name=name,
            description=description,
            run_count=run_count,
            model_version_id=model_version_id,
            default_pool=default_pool,
            default_pool_id=default_pool_id,
            contains_finalized_runs=contains_finalized_runs,
        )

        return project
