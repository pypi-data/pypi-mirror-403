from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.id_and_name import IdAndName


T = TypeVar("T", bound="DataGroup")


@_attrs_define
class DataGroup:
    """
    Attributes:
        id (int | Unset): The id of the data group.
        name (None | str | Unset): The name of the data group, to be used in the API.
        display_name (None | str | Unset): The user-friendly display name of the data group.
        position (int | Unset): Provides a user-friendly ordering of the data groups for the run.
        help_ (None | str | Unset): A url linking to the documentation for this data group.
        owner_run_if_not_owned (IdAndName | Unset):
        version (int | None | Unset): The version of the data in this data group being used by this run.
        revision (int | None | Unset): The revision number of the data. The revision is incremented every time a change
            is made to the
            data in the data group.
        is_in_use (bool | None | Unset): Whether the datagroup is currently in use
    """

    id: int | Unset = UNSET
    name: None | str | Unset = UNSET
    display_name: None | str | Unset = UNSET
    position: int | Unset = UNSET
    help_: None | str | Unset = UNSET
    owner_run_if_not_owned: IdAndName | Unset = UNSET
    version: int | None | Unset = UNSET
    revision: int | None | Unset = UNSET
    is_in_use: bool | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        display_name: None | str | Unset
        if isinstance(self.display_name, Unset):
            display_name = UNSET
        else:
            display_name = self.display_name

        position = self.position

        help_: None | str | Unset
        if isinstance(self.help_, Unset):
            help_ = UNSET
        else:
            help_ = self.help_

        owner_run_if_not_owned: dict[str, Any] | Unset = UNSET
        if not isinstance(self.owner_run_if_not_owned, Unset):
            owner_run_if_not_owned = self.owner_run_if_not_owned.to_dict()

        version: int | None | Unset
        if isinstance(self.version, Unset):
            version = UNSET
        else:
            version = self.version

        revision: int | None | Unset
        if isinstance(self.revision, Unset):
            revision = UNSET
        else:
            revision = self.revision

        is_in_use: bool | None | Unset
        if isinstance(self.is_in_use, Unset):
            is_in_use = UNSET
        else:
            is_in_use = self.is_in_use

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if display_name is not UNSET:
            field_dict["displayName"] = display_name
        if position is not UNSET:
            field_dict["position"] = position
        if help_ is not UNSET:
            field_dict["help"] = help_
        if owner_run_if_not_owned is not UNSET:
            field_dict["ownerRunIfNotOwned"] = owner_run_if_not_owned
        if version is not UNSET:
            field_dict["version"] = version
        if revision is not UNSET:
            field_dict["revision"] = revision
        if is_in_use is not UNSET:
            field_dict["isInUse"] = is_in_use

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.id_and_name import IdAndName

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_display_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        display_name = _parse_display_name(d.pop("displayName", UNSET))

        position = d.pop("position", UNSET)

        def _parse_help_(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        help_ = _parse_help_(d.pop("help", UNSET))

        _owner_run_if_not_owned = d.pop("ownerRunIfNotOwned", UNSET)
        owner_run_if_not_owned: IdAndName | Unset
        if isinstance(_owner_run_if_not_owned, Unset):
            owner_run_if_not_owned = UNSET
        else:
            owner_run_if_not_owned = IdAndName.from_dict(_owner_run_if_not_owned)

        def _parse_version(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        version = _parse_version(d.pop("version", UNSET))

        def _parse_revision(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        revision = _parse_revision(d.pop("revision", UNSET))

        def _parse_is_in_use(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_in_use = _parse_is_in_use(d.pop("isInUse", UNSET))

        data_group = cls(
            id=id,
            name=name,
            display_name=display_name,
            position=position,
            help_=help_,
            owner_run_if_not_owned=owner_run_if_not_owned,
            version=version,
            revision=revision,
            is_in_use=is_in_use,
        )

        return data_group
