from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateWorkspace")


@_attrs_define
class CreateWorkspace:
    """
    Attributes:
        name (None | str): The name of the workspace.
        description (None | str | Unset): The description of the workspace.
        suppress_model_assignment (bool | Unset): If false, all models will be assigned to the workspace. Otherwise no
            models will be assigned to the new workspace.
        suppress_calculation_pool_assignment (bool | Unset): If false, all calculation pools will be assigned to the
            workspace. Otherwise no calculation pools will be assigned to the new workspace.
    """

    name: None | str
    description: None | str | Unset = UNSET
    suppress_model_assignment: bool | Unset = UNSET
    suppress_calculation_pool_assignment: bool | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name: None | str
        name = self.name

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        suppress_model_assignment = self.suppress_model_assignment

        suppress_calculation_pool_assignment = self.suppress_calculation_pool_assignment

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if suppress_model_assignment is not UNSET:
            field_dict["suppressModelAssignment"] = suppress_model_assignment
        if suppress_calculation_pool_assignment is not UNSET:
            field_dict["suppressCalculationPoolAssignment"] = suppress_calculation_pool_assignment

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        name = _parse_name(d.pop("name"))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        suppress_model_assignment = d.pop("suppressModelAssignment", UNSET)

        suppress_calculation_pool_assignment = d.pop("suppressCalculationPoolAssignment", UNSET)

        create_workspace = cls(
            name=name,
            description=description,
            suppress_model_assignment=suppress_model_assignment,
            suppress_calculation_pool_assignment=suppress_calculation_pool_assignment,
        )

        return create_workspace
