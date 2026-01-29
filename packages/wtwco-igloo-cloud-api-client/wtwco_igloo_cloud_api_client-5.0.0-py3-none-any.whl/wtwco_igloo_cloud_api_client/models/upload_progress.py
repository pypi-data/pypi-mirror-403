from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UploadProgress")


@_attrs_define
class UploadProgress:
    """
    Attributes:
        upload_percent (int | Unset): Used to update the service with an indication of how much content has been
            uploaded to Azure blob storage.
            A value of 100 is used to indicate that the file contents has been fully uploaded.
    """

    upload_percent: int | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        upload_percent = self.upload_percent

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if upload_percent is not UNSET:
            field_dict["uploadPercent"] = upload_percent

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        upload_percent = d.pop("uploadPercent", UNSET)

        upload_progress = cls(
            upload_percent=upload_percent,
        )

        return upload_progress
