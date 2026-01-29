from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.update_input_data_table_updates_type_0_additional_property_type_0 import (
        UpdateInputDataTableUpdatesType0AdditionalPropertyType0,
    )


T = TypeVar("T", bound="UpdateInputDataTableUpdatesType0")


@_attrs_define
class UpdateInputDataTableUpdatesType0:
    """A dictionary of table names with the data changes to make to that table.
    The data changes to make to the table are in the form of a dictionary of column names with an associated list of
    values.
    Different columns for the same table must have lists of the same length.

    List tables must have exactly one column name supplied called "Value". The values in the list for this
    column will be used to add new rows to the List table. If a value in the data is already in the list table
    then it is silently ignored so as to support idempotency if the API call is replayed.
    If ReplaceListTables is true then the list table is cleared before the new values are added, allowing old values to
    be removed.
    It is not possible to rename values in list tables using the UpdateInputData API call.

    For other input tables, you must include all of the dimension columns for that table and some of the
    non-dimension columns.
    The values in the dimension columns are used to locate the row to update and the values in the other
    columns are used to update the values there. If a data column is not supplied then the values in that location
    are left unchanged.

    The UpdateInputData API can be called as many times as you like, so you can split up the updates
    by table, by columns or by rows if necessary.

    Note: If the table belongs to a data group that is not owned by this run then the system will automatically
    make a new data group version to contain the modifications to the table.

        Example:
            {'TableName1': {'ColumnName1': ['Value1', 'Value2', '...', 'ValueK'], 'ColumnName2': ['Value1', 'Value2', '...',
                'ValueK']}, 'TableName2': {'ColumnName1': ['Value1', 'Value2', '...', 'ValueL'], 'ColumnName2': ['Value1',
                'Value2', '...', 'ValueL'], 'ColumnName3': ['Value1', 'Value2', '...', 'ValueL']}, 'TableName3': {'ColumnName1':
                ['Value1', 'Value2', '...', 'ValueM']}}

    """

    additional_properties: dict[str, None | UpdateInputDataTableUpdatesType0AdditionalPropertyType0] = _attrs_field(
        init=False, factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        from ..models.update_input_data_table_updates_type_0_additional_property_type_0 import (
            UpdateInputDataTableUpdatesType0AdditionalPropertyType0,
        )

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            if isinstance(prop, UpdateInputDataTableUpdatesType0AdditionalPropertyType0):
                field_dict[prop_name] = prop.to_dict()
            else:
                field_dict[prop_name] = prop

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_input_data_table_updates_type_0_additional_property_type_0 import (
            UpdateInputDataTableUpdatesType0AdditionalPropertyType0,
        )

        d = dict(src_dict)
        update_input_data_table_updates_type_0 = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():

            def _parse_additional_property(
                data: object,
            ) -> None | UpdateInputDataTableUpdatesType0AdditionalPropertyType0:
                if data is None:
                    return data
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    additional_property_type_0 = UpdateInputDataTableUpdatesType0AdditionalPropertyType0.from_dict(data)

                    return additional_property_type_0
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                return cast(None | UpdateInputDataTableUpdatesType0AdditionalPropertyType0, data)

            additional_property = _parse_additional_property(prop_dict)

            additional_properties[prop_name] = additional_property

        update_input_data_table_updates_type_0.additional_properties = additional_properties
        return update_input_data_table_updates_type_0

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> None | UpdateInputDataTableUpdatesType0AdditionalPropertyType0:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: None | UpdateInputDataTableUpdatesType0AdditionalPropertyType0) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
