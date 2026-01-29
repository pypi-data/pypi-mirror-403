from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.model_version_type import ModelVersionType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.workspace_and_projects import WorkspaceAndProjects


T = TypeVar("T", bound="ModelVersion")


@_attrs_define
class ModelVersion:
    """
    Attributes:
        id (int | Unset): The id of this model version which should be used to specify the model version in other API
            calls such as CreateProject.
        name (None | str | Unset): The name for this specific model version.
        model_name (None | str | Unset): The name of the model.
        sem_version (None | str | Unset): The semantic version of this model version.
        description (None | str | Unset): The description of the model version.
        type_ (ModelVersionType | Unset): The model version type. This can be one of the following values:
             * WTW - The model version was deployed by WTW and cannot be modified.
             * InDevelopment - The model version is in development and changes to it can be pushed at any time.
             * Finalized - A model version that has been developed by users of the system and is now finalized so that no
            more changes can be made to it.
        upload_time (datetime.datetime | None | Unset): The time that this model version was last uploaded.
        uploaded_by (None | str | Unset): The last user that uploaded this model version.
        workspaces_and_projects (list[WorkspaceAndProjects] | None | Unset): When requested globally returns the set of
            workspace ids that this model version is assigned to with the number of projects in each of those workspaces
            that use it.
    """

    id: int | Unset = UNSET
    name: None | str | Unset = UNSET
    model_name: None | str | Unset = UNSET
    sem_version: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    type_: ModelVersionType | Unset = UNSET
    upload_time: datetime.datetime | None | Unset = UNSET
    uploaded_by: None | str | Unset = UNSET
    workspaces_and_projects: list[WorkspaceAndProjects] | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        model_name: None | str | Unset
        if isinstance(self.model_name, Unset):
            model_name = UNSET
        else:
            model_name = self.model_name

        sem_version: None | str | Unset
        if isinstance(self.sem_version, Unset):
            sem_version = UNSET
        else:
            sem_version = self.sem_version

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        upload_time: None | str | Unset
        if isinstance(self.upload_time, Unset):
            upload_time = UNSET
        elif isinstance(self.upload_time, datetime.datetime):
            upload_time = self.upload_time.isoformat()
        else:
            upload_time = self.upload_time

        uploaded_by: None | str | Unset
        if isinstance(self.uploaded_by, Unset):
            uploaded_by = UNSET
        else:
            uploaded_by = self.uploaded_by

        workspaces_and_projects: list[dict[str, Any]] | None | Unset
        if isinstance(self.workspaces_and_projects, Unset):
            workspaces_and_projects = UNSET
        elif isinstance(self.workspaces_and_projects, list):
            workspaces_and_projects = []
            for workspaces_and_projects_type_0_item_data in self.workspaces_and_projects:
                workspaces_and_projects_type_0_item = workspaces_and_projects_type_0_item_data.to_dict()
                workspaces_and_projects.append(workspaces_and_projects_type_0_item)

        else:
            workspaces_and_projects = self.workspaces_and_projects

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if model_name is not UNSET:
            field_dict["modelName"] = model_name
        if sem_version is not UNSET:
            field_dict["semVersion"] = sem_version
        if description is not UNSET:
            field_dict["description"] = description
        if type_ is not UNSET:
            field_dict["type"] = type_
        if upload_time is not UNSET:
            field_dict["uploadTime"] = upload_time
        if uploaded_by is not UNSET:
            field_dict["uploadedBy"] = uploaded_by
        if workspaces_and_projects is not UNSET:
            field_dict["workspacesAndProjects"] = workspaces_and_projects

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.workspace_and_projects import WorkspaceAndProjects

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_model_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        model_name = _parse_model_name(d.pop("modelName", UNSET))

        def _parse_sem_version(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        sem_version = _parse_sem_version(d.pop("semVersion", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        _type_ = d.pop("type", UNSET)
        type_: ModelVersionType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = ModelVersionType(_type_)

        def _parse_upload_time(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                upload_time_type_0 = isoparse(data)

                return upload_time_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        upload_time = _parse_upload_time(d.pop("uploadTime", UNSET))

        def _parse_uploaded_by(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        uploaded_by = _parse_uploaded_by(d.pop("uploadedBy", UNSET))

        def _parse_workspaces_and_projects(data: object) -> list[WorkspaceAndProjects] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                workspaces_and_projects_type_0 = []
                _workspaces_and_projects_type_0 = data
                for workspaces_and_projects_type_0_item_data in _workspaces_and_projects_type_0:
                    workspaces_and_projects_type_0_item = WorkspaceAndProjects.from_dict(
                        workspaces_and_projects_type_0_item_data
                    )

                    workspaces_and_projects_type_0.append(workspaces_and_projects_type_0_item)

                return workspaces_and_projects_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[WorkspaceAndProjects] | None | Unset, data)

        workspaces_and_projects = _parse_workspaces_and_projects(d.pop("workspacesAndProjects", UNSET))

        model_version = cls(
            id=id,
            name=name,
            model_name=model_name,
            sem_version=sem_version,
            description=description,
            type_=type_,
            upload_time=upload_time,
            uploaded_by=uploaded_by,
            workspaces_and_projects=workspaces_and_projects,
        )

        return model_version
