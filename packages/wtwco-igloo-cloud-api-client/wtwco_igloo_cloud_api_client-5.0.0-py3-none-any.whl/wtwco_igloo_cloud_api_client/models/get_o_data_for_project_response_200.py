from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_o_data_for_project_response_200_value_item import GetODataForProjectResponse200ValueItem


T = TypeVar("T", bound="GetODataForProjectResponse200")


@_attrs_define
class GetODataForProjectResponse200:
    """
    Attributes:
        odata_context (str | Unset): A link to the metatadata for this table
        value (list[GetODataForProjectResponse200ValueItem] | Unset): The data for the table. The types of properties
            will depend on the table being selected from and the columns requested by $select
    """

    odata_context: str | Unset = UNSET
    value: list[GetODataForProjectResponse200ValueItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        odata_context = self.odata_context

        value: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.value, Unset):
            value = []
            for value_item_data in self.value:
                value_item = value_item_data.to_dict()
                value.append(value_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if odata_context is not UNSET:
            field_dict["@odata.context"] = odata_context
        if value is not UNSET:
            field_dict["value"] = value

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_o_data_for_project_response_200_value_item import GetODataForProjectResponse200ValueItem

        d = dict(src_dict)
        odata_context = d.pop("@odata.context", UNSET)

        _value = d.pop("value", UNSET)
        value: list[GetODataForProjectResponse200ValueItem] | Unset = UNSET
        if _value is not UNSET:
            value = []
            for value_item_data in _value:
                value_item = GetODataForProjectResponse200ValueItem.from_dict(value_item_data)

                value.append(value_item)

        get_o_data_for_project_response_200 = cls(
            odata_context=odata_context,
            value=value,
        )

        get_o_data_for_project_response_200.additional_properties = d
        return get_o_data_for_project_response_200

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
