from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.auto_start_schedule import AutoStartSchedule


T = TypeVar("T", bound="CalculationPoolAutoStartConfiguration")


@_attrs_define
class CalculationPoolAutoStartConfiguration:
    """
    Attributes:
        auto_start_schedules (list[AutoStartSchedule] | None): The list of auto start schedules that should be used for
            Igloo Cloud
    """

    auto_start_schedules: list[AutoStartSchedule] | None

    def to_dict(self) -> dict[str, Any]:
        auto_start_schedules: list[dict[str, Any]] | None
        if isinstance(self.auto_start_schedules, list):
            auto_start_schedules = []
            for auto_start_schedules_type_0_item_data in self.auto_start_schedules:
                auto_start_schedules_type_0_item = auto_start_schedules_type_0_item_data.to_dict()
                auto_start_schedules.append(auto_start_schedules_type_0_item)

        else:
            auto_start_schedules = self.auto_start_schedules

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "autoStartSchedules": auto_start_schedules,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.auto_start_schedule import AutoStartSchedule

        d = dict(src_dict)

        def _parse_auto_start_schedules(data: object) -> list[AutoStartSchedule] | None:
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                auto_start_schedules_type_0 = []
                _auto_start_schedules_type_0 = data
                for auto_start_schedules_type_0_item_data in _auto_start_schedules_type_0:
                    auto_start_schedules_type_0_item = AutoStartSchedule.from_dict(
                        auto_start_schedules_type_0_item_data
                    )

                    auto_start_schedules_type_0.append(auto_start_schedules_type_0_item)

                return auto_start_schedules_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[AutoStartSchedule] | None, data)

        auto_start_schedules = _parse_auto_start_schedules(d.pop("autoStartSchedules"))

        calculation_pool_auto_start_configuration = cls(
            auto_start_schedules=auto_start_schedules,
        )

        return calculation_pool_auto_start_configuration
