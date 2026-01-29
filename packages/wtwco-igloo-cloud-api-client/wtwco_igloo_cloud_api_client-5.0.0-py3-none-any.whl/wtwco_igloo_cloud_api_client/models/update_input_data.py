from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.numeric_date_format import NumericDateFormat
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_input_data_table_updates_type_0 import UpdateInputDataTableUpdatesType0
    from ..models.update_input_data_table_updates_with_mapping_type_0 import UpdateInputDataTableUpdatesWithMappingType0


T = TypeVar("T", bound="UpdateInputData")


@_attrs_define
class UpdateInputData:
    """
    Attributes:
        table_updates (None | Unset | UpdateInputDataTableUpdatesType0): A dictionary of table names with the data
            changes to make to that table.
            The data changes to make to the table are in the form of a dictionary of column names with an associated list of
            values.
            Different columns for the same table must have lists of the same length.

            List tables must have exactly one column name supplied called "Value". The values in the list for this
            column will be used to add new rows to the List table. If a value in the data is already in the list table
            then it is silently ignored so as to support idempotency if the API call is replayed.
            If ReplaceListTables is true then the list table is cleared before the new values are added, allowing old values
            to be removed.
            It is not possible to rename values in list tables using the UpdateInputData API call.

            For other input tables, you must include all of the dimension columns for that table and some of the
            non-dimension columns.
            The values in the dimension columns are used to locate the row to update and the values in the other
            columns are used to update the values there. If a data column is not supplied then the values in that location
            are left unchanged.

            The UpdateInputData API can be called as many times as you like, so you can split up the updates
            by table, by columns or by rows if necessary.

            Note: If the table belongs to a data group that is not owned by this run then the system will automatically
            make a new data group version to contain the modifications to the table. Example: {'TableName1': {'ColumnName1':
            ['Value1', 'Value2', '...', 'ValueK'], 'ColumnName2': ['Value1', 'Value2', '...', 'ValueK']}, 'TableName2':
            {'ColumnName1': ['Value1', 'Value2', '...', 'ValueL'], 'ColumnName2': ['Value1', 'Value2', '...', 'ValueL'],
            'ColumnName3': ['Value1', 'Value2', '...', 'ValueL']}, 'TableName3': {'ColumnName1': ['Value1', 'Value2', '...',
            'ValueM']}}.
        replace_list_tables (bool | Unset): If true then any old values in list tables that are not in the new list
            supplied will be removed.
        error_if_whole_table_not_updated (bool | Unset): If true then the API will return an error if not every cell in
            a data table is updated.
        numeric_date_format (NumericDateFormat | Unset): An enum which lets you choose how and whether numbers are
            converted to dates
        table_updates_with_mapping (None | Unset | UpdateInputDataTableUpdatesWithMappingType0): A dictionary of table
            names and data changes to make to that table in the form of a 2-dimension rectangle of values and a description
            of how to map the values into the table. Example: {'TableName1': {'dataWithHeaders': [['', 'ValueField1',
            'ValueField2'], ['DimensionValue1', 'Value11', 'Value21'], ['DimensionValue2', 'Value12', 'Value22']],
            'dataLayout': {'dimensions': {'DimensionName1': {'axis': 'Column', 'axisOrder': 0}}, 'valueFields': {'axis':
            'Row', 'axisOrder': 0}}}}.
    """

    table_updates: None | Unset | UpdateInputDataTableUpdatesType0 = UNSET
    replace_list_tables: bool | Unset = UNSET
    error_if_whole_table_not_updated: bool | Unset = UNSET
    numeric_date_format: NumericDateFormat | Unset = UNSET
    table_updates_with_mapping: None | Unset | UpdateInputDataTableUpdatesWithMappingType0 = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.update_input_data_table_updates_type_0 import UpdateInputDataTableUpdatesType0
        from ..models.update_input_data_table_updates_with_mapping_type_0 import (
            UpdateInputDataTableUpdatesWithMappingType0,
        )

        table_updates: dict[str, Any] | None | Unset
        if isinstance(self.table_updates, Unset):
            table_updates = UNSET
        elif isinstance(self.table_updates, UpdateInputDataTableUpdatesType0):
            table_updates = self.table_updates.to_dict()
        else:
            table_updates = self.table_updates

        replace_list_tables = self.replace_list_tables

        error_if_whole_table_not_updated = self.error_if_whole_table_not_updated

        numeric_date_format: str | Unset = UNSET
        if not isinstance(self.numeric_date_format, Unset):
            numeric_date_format = self.numeric_date_format.value

        table_updates_with_mapping: dict[str, Any] | None | Unset
        if isinstance(self.table_updates_with_mapping, Unset):
            table_updates_with_mapping = UNSET
        elif isinstance(self.table_updates_with_mapping, UpdateInputDataTableUpdatesWithMappingType0):
            table_updates_with_mapping = self.table_updates_with_mapping.to_dict()
        else:
            table_updates_with_mapping = self.table_updates_with_mapping

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if table_updates is not UNSET:
            field_dict["tableUpdates"] = table_updates
        if replace_list_tables is not UNSET:
            field_dict["replaceListTables"] = replace_list_tables
        if error_if_whole_table_not_updated is not UNSET:
            field_dict["errorIfWholeTableNotUpdated"] = error_if_whole_table_not_updated
        if numeric_date_format is not UNSET:
            field_dict["numericDateFormat"] = numeric_date_format
        if table_updates_with_mapping is not UNSET:
            field_dict["tableUpdatesWithMapping"] = table_updates_with_mapping

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_input_data_table_updates_type_0 import UpdateInputDataTableUpdatesType0
        from ..models.update_input_data_table_updates_with_mapping_type_0 import (
            UpdateInputDataTableUpdatesWithMappingType0,
        )

        d = dict(src_dict)

        def _parse_table_updates(data: object) -> None | Unset | UpdateInputDataTableUpdatesType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                table_updates_type_0 = UpdateInputDataTableUpdatesType0.from_dict(data)

                return table_updates_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UpdateInputDataTableUpdatesType0, data)

        table_updates = _parse_table_updates(d.pop("tableUpdates", UNSET))

        replace_list_tables = d.pop("replaceListTables", UNSET)

        error_if_whole_table_not_updated = d.pop("errorIfWholeTableNotUpdated", UNSET)

        _numeric_date_format = d.pop("numericDateFormat", UNSET)
        numeric_date_format: NumericDateFormat | Unset
        if isinstance(_numeric_date_format, Unset):
            numeric_date_format = UNSET
        else:
            numeric_date_format = NumericDateFormat(_numeric_date_format)

        def _parse_table_updates_with_mapping(
            data: object,
        ) -> None | Unset | UpdateInputDataTableUpdatesWithMappingType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                table_updates_with_mapping_type_0 = UpdateInputDataTableUpdatesWithMappingType0.from_dict(data)

                return table_updates_with_mapping_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UpdateInputDataTableUpdatesWithMappingType0, data)

        table_updates_with_mapping = _parse_table_updates_with_mapping(d.pop("tableUpdatesWithMapping", UNSET))

        update_input_data = cls(
            table_updates=table_updates,
            replace_list_tables=replace_list_tables,
            error_if_whole_table_not_updated=error_if_whole_table_not_updated,
            numeric_date_format=numeric_date_format,
            table_updates_with_mapping=table_updates_with_mapping,
        )

        return update_input_data
