from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="Links")


@_attrs_define
class Links:
    """Provides links for a resource.

    Attributes:
        self_ (None | str | Unset): The self link
    """

    self_: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        self_: None | str | Unset
        if isinstance(self.self_, Unset):
            self_ = UNSET
        else:
            self_ = self.self_

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if self_ is not UNSET:
            field_dict["self"] = self_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_self_(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        self_ = _parse_self_(d.pop("self", UNSET))

        links = cls(
            self_=self_,
        )

        return links
