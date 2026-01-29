from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.table_layout_axis import TableLayoutAxis

T = TypeVar("T", bound="TableLayoutItemPosition")


@_attrs_define
class TableLayoutItemPosition:
    """
    Attributes:
        axis (TableLayoutAxis):
        axis_order (int): The relative order of this item compared to other items on this axis
    """

    axis: TableLayoutAxis
    axis_order: int

    def to_dict(self) -> dict[str, Any]:
        axis = self.axis.value

        axis_order = self.axis_order

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "axis": axis,
                "axisOrder": axis_order,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        axis = TableLayoutAxis(d.pop("axis"))

        axis_order = d.pop("axisOrder")

        table_layout_item_position = cls(
            axis=axis,
            axis_order=axis_order,
        )

        return table_layout_item_position
