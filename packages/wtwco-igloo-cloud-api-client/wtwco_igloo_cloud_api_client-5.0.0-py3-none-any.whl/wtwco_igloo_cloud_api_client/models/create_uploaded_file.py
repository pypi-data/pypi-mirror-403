from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateUploadedFile")


@_attrs_define
class CreateUploadedFile:
    """
    Attributes:
        name (str): The unique name to give to the new file that will be uploaded.
        extension (str): The file extension of the new file to be uploaded, e.g. ".csv"
        description (None | str | Unset): The description for the new file.
        make_name_unique (bool | None | Unset): If true, the system will generate a unique name for this file.
        associated_run_id (int | None | Unset): If set and MakeNameUnique is true, the system will use the associated
            run to generate a unique name for this file.
    """

    name: str
    extension: str
    description: None | str | Unset = UNSET
    make_name_unique: bool | None | Unset = UNSET
    associated_run_id: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        extension = self.extension

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        make_name_unique: bool | None | Unset
        if isinstance(self.make_name_unique, Unset):
            make_name_unique = UNSET
        else:
            make_name_unique = self.make_name_unique

        associated_run_id: int | None | Unset
        if isinstance(self.associated_run_id, Unset):
            associated_run_id = UNSET
        else:
            associated_run_id = self.associated_run_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "extension": extension,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if make_name_unique is not UNSET:
            field_dict["makeNameUnique"] = make_name_unique
        if associated_run_id is not UNSET:
            field_dict["associatedRunId"] = associated_run_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        extension = d.pop("extension")

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_make_name_unique(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        make_name_unique = _parse_make_name_unique(d.pop("makeNameUnique", UNSET))

        def _parse_associated_run_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        associated_run_id = _parse_associated_run_id(d.pop("associatedRunId", UNSET))

        create_uploaded_file = cls(
            name=name,
            extension=extension,
            description=description,
            make_name_unique=make_name_unique,
            associated_run_id=associated_run_id,
        )

        return create_uploaded_file
