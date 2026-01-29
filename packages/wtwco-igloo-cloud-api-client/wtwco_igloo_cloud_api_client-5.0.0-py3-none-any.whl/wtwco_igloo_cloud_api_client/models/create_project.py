from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateProject")


@_attrs_define
class CreateProject:
    """
    Attributes:
        name (str): The name to give to the new project, this must be unique.
        model_version_id (int): The id value of the model version to use in this project. Call GetModels for the list of
            model versions available.
        description (None | str | Unset): The description for the new project.
        source_run_id (int | None | Unset): (optional) The id value of an existing run. If specified the new project
            will create a base run
            containing a copy of the data from this run.
        source_project_id (int | None | Unset): (optional) The id value of an existing project. If specified the new
            project will create a project with a clone of
            all the runs from the source project.
        default_pool (None | str | Unset): The default pool for the project.
        default_pool_id (int | None | Unset): The default pool id for the project. Use this instead of DefaultPool to
            specify the pool by id.
        source_workspace_id (int | None | Unset): (optional) The id value of the workspace to copy from if the source
            run or project is in a different workspace.
    """

    name: str
    model_version_id: int
    description: None | str | Unset = UNSET
    source_run_id: int | None | Unset = UNSET
    source_project_id: int | None | Unset = UNSET
    default_pool: None | str | Unset = UNSET
    default_pool_id: int | None | Unset = UNSET
    source_workspace_id: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        model_version_id = self.model_version_id

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        source_run_id: int | None | Unset
        if isinstance(self.source_run_id, Unset):
            source_run_id = UNSET
        else:
            source_run_id = self.source_run_id

        source_project_id: int | None | Unset
        if isinstance(self.source_project_id, Unset):
            source_project_id = UNSET
        else:
            source_project_id = self.source_project_id

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

        source_workspace_id: int | None | Unset
        if isinstance(self.source_workspace_id, Unset):
            source_workspace_id = UNSET
        else:
            source_workspace_id = self.source_workspace_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "modelVersionId": model_version_id,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if source_run_id is not UNSET:
            field_dict["sourceRunId"] = source_run_id
        if source_project_id is not UNSET:
            field_dict["sourceProjectId"] = source_project_id
        if default_pool is not UNSET:
            field_dict["defaultPool"] = default_pool
        if default_pool_id is not UNSET:
            field_dict["defaultPoolId"] = default_pool_id
        if source_workspace_id is not UNSET:
            field_dict["sourceWorkspaceId"] = source_workspace_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        model_version_id = d.pop("modelVersionId")

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_source_run_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        source_run_id = _parse_source_run_id(d.pop("sourceRunId", UNSET))

        def _parse_source_project_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        source_project_id = _parse_source_project_id(d.pop("sourceProjectId", UNSET))

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

        def _parse_source_workspace_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        source_workspace_id = _parse_source_workspace_id(d.pop("sourceWorkspaceId", UNSET))

        create_project = cls(
            name=name,
            model_version_id=model_version_id,
            description=description,
            source_run_id=source_run_id,
            source_project_id=source_project_id,
            default_pool=default_pool,
            default_pool_id=default_pool_id,
            source_workspace_id=source_workspace_id,
        )

        return create_project
