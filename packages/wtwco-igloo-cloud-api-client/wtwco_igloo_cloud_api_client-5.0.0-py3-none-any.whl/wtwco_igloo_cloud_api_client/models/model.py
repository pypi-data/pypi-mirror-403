from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.model_version import ModelVersion


T = TypeVar("T", bound="Model")


@_attrs_define
class Model:
    """
    Attributes:
        name (None | str | Unset): The name of the model.
        versions (list[ModelVersion] | None | Unset): The list of available versions for this model.
    """

    name: None | str | Unset = UNSET
    versions: list[ModelVersion] | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        versions: list[dict[str, Any]] | None | Unset
        if isinstance(self.versions, Unset):
            versions = UNSET
        elif isinstance(self.versions, list):
            versions = []
            for versions_type_0_item_data in self.versions:
                versions_type_0_item = versions_type_0_item_data.to_dict()
                versions.append(versions_type_0_item)

        else:
            versions = self.versions

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if versions is not UNSET:
            field_dict["versions"] = versions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.model_version import ModelVersion

        d = dict(src_dict)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_versions(data: object) -> list[ModelVersion] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                versions_type_0 = []
                _versions_type_0 = data
                for versions_type_0_item_data in _versions_type_0:
                    versions_type_0_item = ModelVersion.from_dict(versions_type_0_item_data)

                    versions_type_0.append(versions_type_0_item)

                return versions_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[ModelVersion] | None | Unset, data)

        versions = _parse_versions(d.pop("versions", UNSET))

        model = cls(
            name=name,
            versions=versions,
        )

        return model
