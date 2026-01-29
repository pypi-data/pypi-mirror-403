from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="RunResult")


@_attrs_define
class RunResult:
    """
    Attributes:
        name (None | str | Unset): The name of the run result, to be used in the API.
        display_name (None | str | Unset): The user-friendly display name of the run result.
        is_in_use (bool | Unset): Set to true if the run is calculated and the model generated some output for this run
            result.
        help_ (None | str | Unset): The link to the documentation for this run result.
    """

    name: None | str | Unset = UNSET
    display_name: None | str | Unset = UNSET
    is_in_use: bool | Unset = UNSET
    help_: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
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

        is_in_use = self.is_in_use

        help_: None | str | Unset
        if isinstance(self.help_, Unset):
            help_ = UNSET
        else:
            help_ = self.help_

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if display_name is not UNSET:
            field_dict["displayName"] = display_name
        if is_in_use is not UNSET:
            field_dict["isInUse"] = is_in_use
        if help_ is not UNSET:
            field_dict["help"] = help_

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

        def _parse_display_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        display_name = _parse_display_name(d.pop("displayName", UNSET))

        is_in_use = d.pop("isInUse", UNSET)

        def _parse_help_(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        help_ = _parse_help_(d.pop("help", UNSET))

        run_result = cls(
            name=name,
            display_name=display_name,
            is_in_use=is_in_use,
            help_=help_,
        )

        return run_result
