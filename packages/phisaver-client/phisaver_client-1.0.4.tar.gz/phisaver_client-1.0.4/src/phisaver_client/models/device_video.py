from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeviceVideo")


@_attrs_define
class DeviceVideo:
    """
    Attributes:
        id (int):
        name (str):
        url (str):
        created (datetime.datetime):
        thumbnail (str | Unset):
        description (str | Unset):
        device (int | None | Unset):
        fleet (int | None | Unset):
    """

    id: int
    name: str
    url: str
    created: datetime.datetime
    thumbnail: str | Unset = UNSET
    description: str | Unset = UNSET
    device: int | None | Unset = UNSET
    fleet: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        url = self.url

        created = self.created.isoformat()

        thumbnail = self.thumbnail

        description = self.description

        device: int | None | Unset
        if isinstance(self.device, Unset):
            device = UNSET
        else:
            device = self.device

        fleet: int | None | Unset
        if isinstance(self.fleet, Unset):
            fleet = UNSET
        else:
            fleet = self.fleet

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "url": url,
                "created": created,
            }
        )
        if thumbnail is not UNSET:
            field_dict["thumbnail"] = thumbnail
        if description is not UNSET:
            field_dict["description"] = description
        if device is not UNSET:
            field_dict["device"] = device
        if fleet is not UNSET:
            field_dict["fleet"] = fleet

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        url = d.pop("url")

        created = isoparse(d.pop("created"))

        thumbnail = d.pop("thumbnail", UNSET)

        description = d.pop("description", UNSET)

        def _parse_device(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        device = _parse_device(d.pop("device", UNSET))

        def _parse_fleet(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        fleet = _parse_fleet(d.pop("fleet", UNSET))

        device_video = cls(
            id=id,
            name=name,
            url=url,
            created=created,
            thumbnail=thumbnail,
            description=description,
            device=device,
            fleet=fleet,
        )

        device_video.additional_properties = d
        return device_video

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
