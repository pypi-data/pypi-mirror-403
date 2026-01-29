from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="BackupInformation")


@_attrs_define
class BackupInformation:
    """
    Attributes:
        container_name (str):
        blob_name (str):
    """

    container_name: str
    blob_name: str

    def to_dict(self) -> dict[str, Any]:
        container_name = self.container_name

        blob_name = self.blob_name

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "containerName": container_name,
                "blobName": blob_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        container_name = d.pop("containerName")

        blob_name = d.pop("blobName")

        backup_information = cls(
            container_name=container_name,
            blob_name=blob_name,
        )

        return backup_information
