from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateProject")


@_attrs_define
class UpdateProject:
    """
    Attributes:
        name (None | str | Unset): The new name for the project, this must be unique.
        description (None | str | Unset): The new description for the project.
        default_pool (None | str | Unset): The new default pool for the project.
            Assign this to empty string to request that the default pool be removed.
        default_pool_id (int | None | Unset): The new default pool id for the project. Use this instead of DefaultPool
            to specify the pool by id.
            Assign this to zero to request that the default pool be removed.
    """

    name: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    default_pool: None | str | Unset = UNSET
    default_pool_id: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
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

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if default_pool is not UNSET:
            field_dict["defaultPool"] = default_pool
        if default_pool_id is not UNSET:
            field_dict["defaultPoolId"] = default_pool_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

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

        update_project = cls(
            name=name,
            description=description,
            default_pool=default_pool,
            default_pool_id=default_pool_id,
        )

        return update_project
