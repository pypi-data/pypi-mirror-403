from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.calculation_pool_auto_start_configuration import CalculationPoolAutoStartConfiguration


T = TypeVar("T", bound="CalculationPool")


@_attrs_define
class CalculationPool:
    """
    Attributes:
        id (int | Unset): The id value of this calculation pool.
        name (None | str | Unset): The name of a pool that is available to use in Igloo Cloud.
        auto_start_configuration (CalculationPoolAutoStartConfiguration | Unset):
        igloo_version (None | str | Unset): The Igloo version associated with this calculation pool.
        cores (int | Unset): The number of processor cores available in this calculation pool.
        memory_in_gi_b (int | Unset): The amount of memory available in this calculation pool, measured in gibibytes
            (GiB).
        maximum_machines (int | Unset): The maximum number of machines that can be used in this calculation pool.
        tasks_per_machine (int | Unset): The number of tasks that can be executed per machine in this calculation pool.
    """

    id: int | Unset = UNSET
    name: None | str | Unset = UNSET
    auto_start_configuration: CalculationPoolAutoStartConfiguration | Unset = UNSET
    igloo_version: None | str | Unset = UNSET
    cores: int | Unset = UNSET
    memory_in_gi_b: int | Unset = UNSET
    maximum_machines: int | Unset = UNSET
    tasks_per_machine: int | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        auto_start_configuration: dict[str, Any] | Unset = UNSET
        if not isinstance(self.auto_start_configuration, Unset):
            auto_start_configuration = self.auto_start_configuration.to_dict()

        igloo_version: None | str | Unset
        if isinstance(self.igloo_version, Unset):
            igloo_version = UNSET
        else:
            igloo_version = self.igloo_version

        cores = self.cores

        memory_in_gi_b = self.memory_in_gi_b

        maximum_machines = self.maximum_machines

        tasks_per_machine = self.tasks_per_machine

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if auto_start_configuration is not UNSET:
            field_dict["autoStartConfiguration"] = auto_start_configuration
        if igloo_version is not UNSET:
            field_dict["iglooVersion"] = igloo_version
        if cores is not UNSET:
            field_dict["cores"] = cores
        if memory_in_gi_b is not UNSET:
            field_dict["memoryInGiB"] = memory_in_gi_b
        if maximum_machines is not UNSET:
            field_dict["maximumMachines"] = maximum_machines
        if tasks_per_machine is not UNSET:
            field_dict["tasksPerMachine"] = tasks_per_machine

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.calculation_pool_auto_start_configuration import CalculationPoolAutoStartConfiguration

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        _auto_start_configuration = d.pop("autoStartConfiguration", UNSET)
        auto_start_configuration: CalculationPoolAutoStartConfiguration | Unset
        if isinstance(_auto_start_configuration, Unset):
            auto_start_configuration = UNSET
        else:
            auto_start_configuration = CalculationPoolAutoStartConfiguration.from_dict(_auto_start_configuration)

        def _parse_igloo_version(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        igloo_version = _parse_igloo_version(d.pop("iglooVersion", UNSET))

        cores = d.pop("cores", UNSET)

        memory_in_gi_b = d.pop("memoryInGiB", UNSET)

        maximum_machines = d.pop("maximumMachines", UNSET)

        tasks_per_machine = d.pop("tasksPerMachine", UNSET)

        calculation_pool = cls(
            id=id,
            name=name,
            auto_start_configuration=auto_start_configuration,
            igloo_version=igloo_version,
            cores=cores,
            memory_in_gi_b=memory_in_gi_b,
            maximum_machines=maximum_machines,
            tasks_per_machine=tasks_per_machine,
        )

        return calculation_pool
