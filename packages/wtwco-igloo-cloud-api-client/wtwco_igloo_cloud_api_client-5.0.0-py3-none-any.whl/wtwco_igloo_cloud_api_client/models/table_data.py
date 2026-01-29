from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.table_read_only_reason_v2 import TableReadOnlyReasonV2
from ..models.table_type import TableType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.column import Column


T = TypeVar("T", bound="TableData")


@_attrs_define
class TableData:
    """
    Attributes:
        self_ (None | str): This provides a self link to the table including the version and revision of data that is
            currently being used for this run.
        help_ (None | str | Unset): A link to the help document for this data table. This will be null if there is no
            help document available.
        table_link (None | str | Unset): A link to use to get and update the data table link information for this data
            table. Will only be present for tables of type InputList and InputTable.
        is_read_only (bool | None | Unset): Indicates whether the data in this table is editable. If it is read-only
            then the ReadOnlyReason supplies more information as to why.
        read_only_reason (TableReadOnlyReasonV2 | Unset): Indicates the reason why the table is read-only. This can be
            one of the following values:
             * None - The table is not read-only.
             * NotCalculated - The table is read-only because some of the dimension values have changed and the table has
            not yet been updated in response.
             * Result - The table is read-only because it contains the results of a model calculation.
        table_type (TableType | Unset): The type of table. The value can be one of
             * InputList - Indicates that the table contains a dynamic list of values which can be added, updated or deleted
            from.
             * InputTable - Indicates the table contains a fixed number of rows, one for each set of values in the dimension
            columns. The values in the rows can be updated.
             * ResultTable - Indicates the table contains results from calculating the model. The values cannot be modified.
             * ComparisonInputList - Indicates that the table represents a comparison of input lists. The values cannot be
            modified.
             * ComparisonInputTable - Indicates that the table represents a comparison of input tables. Unlike a normal
            input table, there is no guarantee that all dimension values are present. The values cannot be modified.
             * ComparisonResultTable - Indicates that the table represents a comparison of result tables. The values cannot
            be modified.
        dimensions (list[Column] | None | Unset): If the table is of type InputTable or ResultTable then this will
            contain the list of columns that are used to define the dimensions of the table.
            If this is an input table and there are no dimension columns then this table will contain just a single row.
        values (list[Column] | None | Unset): This field contains all of the other columns in the table that are not
            dimension columns.
        data (list[list[Any]] | None | Unset): This field contains the data in the table. The data is represented as a
            list of rows and each row contains a list of values with one value per column
            in the table in the order that the columns are defined in the dimension and value fields.
            Use the DataType value in the Column definition to determine the type of each value.
    """

    self_: None | str
    help_: None | str | Unset = UNSET
    table_link: None | str | Unset = UNSET
    is_read_only: bool | None | Unset = UNSET
    read_only_reason: TableReadOnlyReasonV2 | Unset = UNSET
    table_type: TableType | Unset = UNSET
    dimensions: list[Column] | None | Unset = UNSET
    values: list[Column] | None | Unset = UNSET
    data: list[list[Any]] | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        self_: None | str
        self_ = self.self_

        help_: None | str | Unset
        if isinstance(self.help_, Unset):
            help_ = UNSET
        else:
            help_ = self.help_

        table_link: None | str | Unset
        if isinstance(self.table_link, Unset):
            table_link = UNSET
        else:
            table_link = self.table_link

        is_read_only: bool | None | Unset
        if isinstance(self.is_read_only, Unset):
            is_read_only = UNSET
        else:
            is_read_only = self.is_read_only

        read_only_reason: str | Unset = UNSET
        if not isinstance(self.read_only_reason, Unset):
            read_only_reason = self.read_only_reason.value

        table_type: str | Unset = UNSET
        if not isinstance(self.table_type, Unset):
            table_type = self.table_type.value

        dimensions: list[dict[str, Any]] | None | Unset
        if isinstance(self.dimensions, Unset):
            dimensions = UNSET
        elif isinstance(self.dimensions, list):
            dimensions = []
            for dimensions_type_0_item_data in self.dimensions:
                dimensions_type_0_item = dimensions_type_0_item_data.to_dict()
                dimensions.append(dimensions_type_0_item)

        else:
            dimensions = self.dimensions

        values: list[dict[str, Any]] | None | Unset
        if isinstance(self.values, Unset):
            values = UNSET
        elif isinstance(self.values, list):
            values = []
            for values_type_0_item_data in self.values:
                values_type_0_item = values_type_0_item_data.to_dict()
                values.append(values_type_0_item)

        else:
            values = self.values

        data: list[list[Any]] | None | Unset
        if isinstance(self.data, Unset):
            data = UNSET
        elif isinstance(self.data, list):
            data = []
            for data_type_0_item_data in self.data:
                data_type_0_item = data_type_0_item_data

                data.append(data_type_0_item)

        else:
            data = self.data

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "self": self_,
            }
        )
        if help_ is not UNSET:
            field_dict["help"] = help_
        if table_link is not UNSET:
            field_dict["tableLink"] = table_link
        if is_read_only is not UNSET:
            field_dict["isReadOnly"] = is_read_only
        if read_only_reason is not UNSET:
            field_dict["readOnlyReason"] = read_only_reason
        if table_type is not UNSET:
            field_dict["tableType"] = table_type
        if dimensions is not UNSET:
            field_dict["dimensions"] = dimensions
        if values is not UNSET:
            field_dict["values"] = values
        if data is not UNSET:
            field_dict["data"] = data

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.column import Column

        d = dict(src_dict)

        def _parse_self_(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        self_ = _parse_self_(d.pop("self"))

        def _parse_help_(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        help_ = _parse_help_(d.pop("help", UNSET))

        def _parse_table_link(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        table_link = _parse_table_link(d.pop("tableLink", UNSET))

        def _parse_is_read_only(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        is_read_only = _parse_is_read_only(d.pop("isReadOnly", UNSET))

        _read_only_reason = d.pop("readOnlyReason", UNSET)
        read_only_reason: TableReadOnlyReasonV2 | Unset
        if isinstance(_read_only_reason, Unset):
            read_only_reason = UNSET
        else:
            read_only_reason = TableReadOnlyReasonV2(_read_only_reason)

        _table_type = d.pop("tableType", UNSET)
        table_type: TableType | Unset
        if isinstance(_table_type, Unset):
            table_type = UNSET
        else:
            table_type = TableType(_table_type)

        def _parse_dimensions(data: object) -> list[Column] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                dimensions_type_0 = []
                _dimensions_type_0 = data
                for dimensions_type_0_item_data in _dimensions_type_0:
                    dimensions_type_0_item = Column.from_dict(dimensions_type_0_item_data)

                    dimensions_type_0.append(dimensions_type_0_item)

                return dimensions_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[Column] | None | Unset, data)

        dimensions = _parse_dimensions(d.pop("dimensions", UNSET))

        def _parse_values(data: object) -> list[Column] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                values_type_0 = []
                _values_type_0 = data
                for values_type_0_item_data in _values_type_0:
                    values_type_0_item = Column.from_dict(values_type_0_item_data)

                    values_type_0.append(values_type_0_item)

                return values_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[Column] | None | Unset, data)

        values = _parse_values(d.pop("values", UNSET))

        def _parse_data(data: object) -> list[list[Any]] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                data_type_0 = []
                _data_type_0 = data
                for data_type_0_item_data in _data_type_0:
                    data_type_0_item = cast(list[Any], data_type_0_item_data)

                    data_type_0.append(data_type_0_item)

                return data_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[list[Any]] | None | Unset, data)

        data = _parse_data(d.pop("data", UNSET))

        table_data = cls(
            self_=self_,
            help_=help_,
            table_link=table_link,
            is_read_only=is_read_only,
            read_only_reason=read_only_reason,
            table_type=table_type,
            dimensions=dimensions,
            values=values,
            data=data,
        )

        return table_data
