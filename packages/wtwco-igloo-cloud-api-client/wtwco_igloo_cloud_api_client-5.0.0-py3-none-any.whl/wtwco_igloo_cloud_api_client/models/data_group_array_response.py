from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.data_group import DataGroup
    from ..models.message import Message


T = TypeVar("T", bound="DataGroupArrayResponse")


@_attrs_define
class DataGroupArrayResponse:
    """
    Attributes:
        messages (list[Message] | None | Unset):
        result (list[DataGroup] | None | Unset):
    """

    messages: list[Message] | None | Unset = UNSET
    result: list[DataGroup] | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        messages: list[dict[str, Any]] | None | Unset
        if isinstance(self.messages, Unset):
            messages = UNSET
        elif isinstance(self.messages, list):
            messages = []
            for messages_type_0_item_data in self.messages:
                messages_type_0_item = messages_type_0_item_data.to_dict()
                messages.append(messages_type_0_item)

        else:
            messages = self.messages

        result: list[dict[str, Any]] | None | Unset
        if isinstance(self.result, Unset):
            result = UNSET
        elif isinstance(self.result, list):
            result = []
            for result_type_0_item_data in self.result:
                result_type_0_item = result_type_0_item_data.to_dict()
                result.append(result_type_0_item)

        else:
            result = self.result

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if messages is not UNSET:
            field_dict["messages"] = messages
        if result is not UNSET:
            field_dict["result"] = result

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.data_group import DataGroup
        from ..models.message import Message

        d = dict(src_dict)

        def _parse_messages(data: object) -> list[Message] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                messages_type_0 = []
                _messages_type_0 = data
                for messages_type_0_item_data in _messages_type_0:
                    messages_type_0_item = Message.from_dict(messages_type_0_item_data)

                    messages_type_0.append(messages_type_0_item)

                return messages_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[Message] | None | Unset, data)

        messages = _parse_messages(d.pop("messages", UNSET))

        def _parse_result(data: object) -> list[DataGroup] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                result_type_0 = []
                _result_type_0 = data
                for result_type_0_item_data in _result_type_0:
                    result_type_0_item = DataGroup.from_dict(result_type_0_item_data)

                    result_type_0.append(result_type_0_item)

                return result_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[DataGroup] | None | Unset, data)

        result = _parse_result(d.pop("result", UNSET))

        data_group_array_response = cls(
            messages=messages,
            result=result,
        )

        return data_group_array_response
