from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.table_layout_dimensions_type_0 import TableLayoutDimensionsType0
    from ..models.table_layout_item_position import TableLayoutItemPosition


T = TypeVar("T", bound="TableLayout")


@_attrs_define
class TableLayout:
    """
    Attributes:
        dimensions (None | TableLayoutDimensionsType0 | Unset): Describes the arrangement of the dimensions, indexed by
            the dimension name
        value_fields (TableLayoutItemPosition | Unset):
    """

    dimensions: None | TableLayoutDimensionsType0 | Unset = UNSET
    value_fields: TableLayoutItemPosition | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.table_layout_dimensions_type_0 import TableLayoutDimensionsType0

        dimensions: dict[str, Any] | None | Unset
        if isinstance(self.dimensions, Unset):
            dimensions = UNSET
        elif isinstance(self.dimensions, TableLayoutDimensionsType0):
            dimensions = self.dimensions.to_dict()
        else:
            dimensions = self.dimensions

        value_fields: dict[str, Any] | Unset = UNSET
        if not isinstance(self.value_fields, Unset):
            value_fields = self.value_fields.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if dimensions is not UNSET:
            field_dict["dimensions"] = dimensions
        if value_fields is not UNSET:
            field_dict["valueFields"] = value_fields

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.table_layout_dimensions_type_0 import TableLayoutDimensionsType0
        from ..models.table_layout_item_position import TableLayoutItemPosition

        d = dict(src_dict)

        def _parse_dimensions(data: object) -> None | TableLayoutDimensionsType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                dimensions_type_0 = TableLayoutDimensionsType0.from_dict(data)

                return dimensions_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TableLayoutDimensionsType0 | Unset, data)

        dimensions = _parse_dimensions(d.pop("dimensions", UNSET))

        _value_fields = d.pop("valueFields", UNSET)
        value_fields: TableLayoutItemPosition | Unset
        if isinstance(_value_fields, Unset):
            value_fields = UNSET
        else:
            value_fields = TableLayoutItemPosition.from_dict(_value_fields)

        table_layout = cls(
            dimensions=dimensions,
            value_fields=value_fields,
        )

        return table_layout
