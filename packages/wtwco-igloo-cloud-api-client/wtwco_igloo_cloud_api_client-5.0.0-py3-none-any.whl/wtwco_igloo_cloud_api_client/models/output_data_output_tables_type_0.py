from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.output_data_output_tables_type_0_additional_property_type_0 import (
        OutputDataOutputTablesType0AdditionalPropertyType0,
    )


T = TypeVar("T", bound="OutputDataOutputTablesType0")


@_attrs_define
class OutputDataOutputTablesType0:
    """Set only if the RunStatus equals Done. Will contain all of the output data for that run, or a single table if
    requested, in the format:

        Example:
            {'TableName1': {'ColumnName1': ['Value1', 'Value2', '...', 'ValueK'], 'ColumnName2': ['Value1', 'Value2', '...',
                'ValueK']}, 'TableName2': {'ColumnName1': ['Value1', 'Value2', '...', 'ValueL'], 'ColumnName2': ['Value1',
                'Value2', '...', 'ValueL'], 'ColumnName3': ['Value1', 'Value2', '...', 'ValueL']}, 'TableName3': {'ColumnName1':
                ['Value1', 'Value2', '...', 'ValueM']}}

    """

    additional_properties: dict[str, None | OutputDataOutputTablesType0AdditionalPropertyType0] = _attrs_field(
        init=False, factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        from ..models.output_data_output_tables_type_0_additional_property_type_0 import (
            OutputDataOutputTablesType0AdditionalPropertyType0,
        )

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            if isinstance(prop, OutputDataOutputTablesType0AdditionalPropertyType0):
                field_dict[prop_name] = prop.to_dict()
            else:
                field_dict[prop_name] = prop

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.output_data_output_tables_type_0_additional_property_type_0 import (
            OutputDataOutputTablesType0AdditionalPropertyType0,
        )

        d = dict(src_dict)
        output_data_output_tables_type_0 = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():

            def _parse_additional_property(data: object) -> None | OutputDataOutputTablesType0AdditionalPropertyType0:
                if data is None:
                    return data
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    additional_property_type_0 = OutputDataOutputTablesType0AdditionalPropertyType0.from_dict(data)

                    return additional_property_type_0
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                return cast(None | OutputDataOutputTablesType0AdditionalPropertyType0, data)

            additional_property = _parse_additional_property(prop_dict)

            additional_properties[prop_name] = additional_property

        output_data_output_tables_type_0.additional_properties = additional_properties
        return output_data_output_tables_type_0

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> None | OutputDataOutputTablesType0AdditionalPropertyType0:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: None | OutputDataOutputTablesType0AdditionalPropertyType0) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
