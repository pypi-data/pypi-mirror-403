from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.calculation_pool import CalculationPool
    from ..models.message import Message


T = TypeVar("T", bound="CalculationPoolResponse")


@_attrs_define
class CalculationPoolResponse:
    """
    Attributes:
        messages (list[Message] | None | Unset):
        result (CalculationPool | Unset):
    """

    messages: list[Message] | None | Unset = UNSET
    result: CalculationPool | Unset = UNSET

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

        result: dict[str, Any] | Unset = UNSET
        if not isinstance(self.result, Unset):
            result = self.result.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if messages is not UNSET:
            field_dict["messages"] = messages
        if result is not UNSET:
            field_dict["result"] = result

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.calculation_pool import CalculationPool
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

        _result = d.pop("result", UNSET)
        result: CalculationPool | Unset
        if isinstance(_result, Unset):
            result = UNSET
        else:
            result = CalculationPool.from_dict(_result)

        calculation_pool_response = cls(
            messages=messages,
            result=result,
        )

        return calculation_pool_response
