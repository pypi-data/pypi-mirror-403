from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateRun")


@_attrs_define
class CreateRun:
    """
    Attributes:
        name (str): The name to give to the new run, this must be unique.
        parent_id (int): The id value for the run that you want to be the parent of this new run.
        description (None | str | Unset): The description for the new run.
        make_name_unique (bool | None | Unset): If true then the system will ensure a unique name for this run is
            generated based on the name property supplied above. Default: False.
        auto_delete_minutes (int | None | Unset): If set, indicates that we wish the system to automatically delete the
            run and all of its data after this many minutes has elapsed.
    """

    name: str
    parent_id: int
    description: None | str | Unset = UNSET
    make_name_unique: bool | None | Unset = False
    auto_delete_minutes: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        parent_id = self.parent_id

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        make_name_unique: bool | None | Unset
        if isinstance(self.make_name_unique, Unset):
            make_name_unique = UNSET
        else:
            make_name_unique = self.make_name_unique

        auto_delete_minutes: int | None | Unset
        if isinstance(self.auto_delete_minutes, Unset):
            auto_delete_minutes = UNSET
        else:
            auto_delete_minutes = self.auto_delete_minutes

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "parentId": parent_id,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if make_name_unique is not UNSET:
            field_dict["makeNameUnique"] = make_name_unique
        if auto_delete_minutes is not UNSET:
            field_dict["autoDeleteMinutes"] = auto_delete_minutes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        parent_id = d.pop("parentId")

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_make_name_unique(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        make_name_unique = _parse_make_name_unique(d.pop("makeNameUnique", UNSET))

        def _parse_auto_delete_minutes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        auto_delete_minutes = _parse_auto_delete_minutes(d.pop("autoDeleteMinutes", UNSET))

        create_run = cls(
            name=name,
            parent_id=parent_id,
            description=description,
            make_name_unique=make_name_unique,
            auto_delete_minutes=auto_delete_minutes,
        )

        return create_run
