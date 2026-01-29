from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="DataTableNode")


@_attrs_define
class DataTableNode:
    """This can be either a folder or a table depending on the type

    Attributes:
        kind (None | str | Unset): What type of node is this e.g. is it a table or a folder
        help_ (None | str | Unset): A link to the help documentation for this node, if it exists
        name (None | str | Unset): The name of this node, this is used for referencing in other HTTP queries
        display_name (None | str | Unset): The display name of this node, e.g. this will make something like
            "CorrelationGroup9" into "Correlation Group 9"
        is_empty (bool | None | Unset): Whether or not the table or tables in the folder are empty.
        children (list[DataTableNode] | None | Unset):
    """

    kind: None | str | Unset = UNSET
    help_: None | str | Unset = UNSET
    name: None | str | Unset = UNSET
    display_name: None | str | Unset = UNSET
    is_empty: bool | None | Unset = UNSET
    children: list[DataTableNode] | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        kind: None | str | Unset
        if isinstance(self.kind, Unset):
            kind = UNSET
        else:
            kind = self.kind

        help_: None | str | Unset
        if isinstance(self.help_, Unset):
            help_ = UNSET
        else:
            help_ = self.help_

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

        is_empty: bool | None | Unset
        if isinstance(self.is_empty, Unset):
            is_empty = UNSET
        else:
            is_empty = self.is_empty

        children: list[dict[str, Any]] | None | Unset
        if isinstance(self.children, Unset):
            children = UNSET
        elif isinstance(self.children, list):
            children = []
            for children_type_0_item_data in self.children:
                children_type_0_item = children_type_0_item_data.to_dict()
                children.append(children_type_0_item)

        else:
            children = self.children

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if kind is not UNSET:
            field_dict["kind"] = kind
        if help_ is not UNSET:
            field_dict["help"] = help_
        if name is not UNSET:
            field_dict["name"] = name
        if display_name is not UNSET:
            field_dict["displayName"] = display_name
        if is_empty is not UNSET:
            field_dict["isEmpty"] = is_empty
        if children is not UNSET:
            field_dict["children"] = children

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_kind(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        kind = _parse_kind(d.pop("kind", UNSET))

        def _parse_help_(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        help_ = _parse_help_(d.pop("help", UNSET))

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

        def _parse_is_empty(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_empty = _parse_is_empty(d.pop("isEmpty", UNSET))

        def _parse_children(data: object) -> list[DataTableNode] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                children_type_0 = []
                _children_type_0 = data
                for children_type_0_item_data in _children_type_0:
                    children_type_0_item = DataTableNode.from_dict(children_type_0_item_data)

                    children_type_0.append(children_type_0_item)

                return children_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[DataTableNode] | None | Unset, data)

        children = _parse_children(d.pop("children", UNSET))

        data_table_node = cls(
            kind=kind,
            help_=help_,
            name=name,
            display_name=display_name,
            is_empty=is_empty,
            children=children,
        )

        return data_table_node
