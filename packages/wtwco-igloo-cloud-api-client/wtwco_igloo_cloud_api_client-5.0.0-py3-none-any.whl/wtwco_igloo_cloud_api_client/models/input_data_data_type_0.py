from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="InputDataDataType0")


@_attrs_define
class InputDataDataType0:
    """A dictionary of column names mapped to a list of values containing the data in the table associated with that
    column.

    """

    additional_properties: dict[str, list[Any] | None] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            if isinstance(prop, list):
                field_dict[prop_name] = prop

            else:
                field_dict[prop_name] = prop

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        input_data_data_type_0 = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():

            def _parse_additional_property(data: object) -> list[Any] | None:
                if data is None:
                    return data
                try:
                    if not isinstance(data, list):
                        raise TypeError()
                    additional_property_type_0 = cast(list[Any], data)

                    return additional_property_type_0
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                return cast(list[Any] | None, data)

            additional_property = _parse_additional_property(prop_dict)

            additional_properties[prop_name] = additional_property

        input_data_data_type_0.additional_properties = additional_properties
        return input_data_data_type_0

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> list[Any] | None:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: list[Any] | None) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
