from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.table_layout import TableLayout


T = TypeVar("T", bound="DataWithMapping")


@_attrs_define
class DataWithMapping:
    """
    Attributes:
        data_with_headers (list[list[Any]]): A 2-dimensional rectangular array of values representing the data to
            populate the table with along with the row and column headers values.
        data_layout (TableLayout | Unset):
        table_link_revision (int | None | Unset): Can be provided to instruct MDS to use the layout defined for the
            table link. If the revision does not match the current revision
            then we will return a 409 Conflict error.

            If both Wtw.ModelDataService.Api.DTO.InputData.DataWithMappingDto.DataLayout and
            Wtw.ModelDataService.Api.DTO.InputData.DataWithMappingDto.TableLinkRevision are provided then we will return a
            400 Bad Request error.
    """

    data_with_headers: list[list[Any]]
    data_layout: TableLayout | Unset = UNSET
    table_link_revision: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        data_with_headers = []
        for data_with_headers_item_data in self.data_with_headers:
            data_with_headers_item = data_with_headers_item_data

            data_with_headers.append(data_with_headers_item)

        data_layout: dict[str, Any] | Unset = UNSET
        if not isinstance(self.data_layout, Unset):
            data_layout = self.data_layout.to_dict()

        table_link_revision: int | None | Unset
        if isinstance(self.table_link_revision, Unset):
            table_link_revision = UNSET
        else:
            table_link_revision = self.table_link_revision

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "dataWithHeaders": data_with_headers,
            }
        )
        if data_layout is not UNSET:
            field_dict["dataLayout"] = data_layout
        if table_link_revision is not UNSET:
            field_dict["tableLinkRevision"] = table_link_revision

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.table_layout import TableLayout

        d = dict(src_dict)
        data_with_headers = []
        _data_with_headers = d.pop("dataWithHeaders")
        for data_with_headers_item_data in _data_with_headers:
            data_with_headers_item = cast(list[Any], data_with_headers_item_data)

            data_with_headers.append(data_with_headers_item)

        _data_layout = d.pop("dataLayout", UNSET)
        data_layout: TableLayout | Unset
        if isinstance(_data_layout, Unset):
            data_layout = UNSET
        else:
            data_layout = TableLayout.from_dict(_data_layout)

        def _parse_table_link_revision(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        table_link_revision = _parse_table_link_revision(d.pop("tableLinkRevision", UNSET))

        data_with_mapping = cls(
            data_with_headers=data_with_headers,
            data_layout=data_layout,
            table_link_revision=table_link_revision,
        )

        return data_with_mapping
