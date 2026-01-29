from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="WorkspaceAndProjects")


@_attrs_define
class WorkspaceAndProjects:
    """
    Attributes:
        workspace_id (int | Unset): The id of the workspace.
        project_count (int | Unset): The number of projects in the workspace.
    """

    workspace_id: int | Unset = UNSET
    project_count: int | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        workspace_id = self.workspace_id

        project_count = self.project_count

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if workspace_id is not UNSET:
            field_dict["workspaceId"] = workspace_id
        if project_count is not UNSET:
            field_dict["projectCount"] = project_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        workspace_id = d.pop("workspaceId", UNSET)

        project_count = d.pop("projectCount", UNSET)

        workspace_and_projects = cls(
            workspace_id=workspace_id,
            project_count=project_count,
        )

        return workspace_and_projects
