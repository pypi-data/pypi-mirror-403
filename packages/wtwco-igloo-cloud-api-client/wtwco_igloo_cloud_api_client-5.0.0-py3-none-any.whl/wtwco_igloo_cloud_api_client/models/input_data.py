from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.input_data_data_type_0 import InputDataDataType0


T = TypeVar("T", bound="InputData")


@_attrs_define
class InputData:
    """
    Attributes:
        data (InputDataDataType0 | None): A dictionary of column names mapped to a list of values containing the data in
            the table associated with that column.
    """

    data: InputDataDataType0 | None

    def to_dict(self) -> dict[str, Any]:
        from ..models.input_data_data_type_0 import InputDataDataType0

        data: dict[str, Any] | None
        if isinstance(self.data, InputDataDataType0):
            data = self.data.to_dict()
        else:
            data = self.data

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "data": data,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.input_data_data_type_0 import InputDataDataType0

        d = dict(src_dict)

        def _parse_data(data: object) -> InputDataDataType0 | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                data_type_0 = InputDataDataType0.from_dict(data)

                return data_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(InputDataDataType0 | None, data)

        data = _parse_data(d.pop("data"))

        input_data = cls(
            data=data,
        )

        return input_data
