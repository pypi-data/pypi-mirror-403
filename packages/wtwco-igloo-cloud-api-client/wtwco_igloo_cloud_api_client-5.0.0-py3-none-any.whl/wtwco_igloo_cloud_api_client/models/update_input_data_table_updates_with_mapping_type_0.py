from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.data_with_mapping import DataWithMapping


T = TypeVar("T", bound="UpdateInputDataTableUpdatesWithMappingType0")


@_attrs_define
class UpdateInputDataTableUpdatesWithMappingType0:
    """A dictionary of table names and data changes to make to that table in the form of a 2-dimension rectangle of values
    and a description of how to map the values into the table.

        Example:
            {'TableName1': {'dataWithHeaders': [['', 'ValueField1', 'ValueField2'], ['DimensionValue1', 'Value11',
                'Value21'], ['DimensionValue2', 'Value12', 'Value22']], 'dataLayout': {'dimensions': {'DimensionName1': {'axis':
                'Column', 'axisOrder': 0}}, 'valueFields': {'axis': 'Row', 'axisOrder': 0}}}}

    """

    additional_properties: dict[str, DataWithMapping] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            field_dict[prop_name] = prop.to_dict()

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.data_with_mapping import DataWithMapping

        d = dict(src_dict)
        update_input_data_table_updates_with_mapping_type_0 = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():
            additional_property = DataWithMapping.from_dict(prop_dict)

            additional_properties[prop_name] = additional_property

        update_input_data_table_updates_with_mapping_type_0.additional_properties = additional_properties
        return update_input_data_table_updates_with_mapping_type_0

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> DataWithMapping:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: DataWithMapping) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
