from __future__ import annotations

import json
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from .. import types

if TYPE_CHECKING:
    from ..models.fleet_devices_details import FleetDevicesDetails


T = TypeVar("T", bound="Fleet")


@_attrs_define
class Fleet:
    """
    Attributes:
        id (int):
        ref (str):
        name (str):
        devices (list[str]):
        timezone (str):
        devices_refs (list[str]): Return a list of device refs
        devices_details (FleetDevicesDetails): Return a list of device names, id, etc.
    """

    id: int
    ref: str
    name: str
    devices: list[str]
    timezone: str
    devices_refs: list[str]
    devices_details: FleetDevicesDetails
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        ref = self.ref

        name = self.name

        devices = self.devices

        timezone = self.timezone

        devices_refs = self.devices_refs

        devices_details = self.devices_details.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "ref": ref,
                "name": name,
                "devices": devices,
                "timezone": timezone,
                "devices_refs": devices_refs,
                "devices_details": devices_details,
            }
        )

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(("id", (None, str(self.id).encode(), "text/plain")))

        files.append(("ref", (None, str(self.ref).encode(), "text/plain")))

        files.append(("name", (None, str(self.name).encode(), "text/plain")))

        for devices_item_element in self.devices:
            files.append(("devices", (None, str(devices_item_element).encode(), "text/plain")))

        files.append(("timezone", (None, str(self.timezone).encode(), "text/plain")))

        for devices_refs_item_element in self.devices_refs:
            files.append(("devices_refs", (None, str(devices_refs_item_element).encode(), "text/plain")))

        files.append(
            ("devices_details", (None, json.dumps(self.devices_details.to_dict()).encode(), "application/json"))
        )

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.fleet_devices_details import FleetDevicesDetails

        d = dict(src_dict)
        id = d.pop("id")

        ref = d.pop("ref")

        name = d.pop("name")

        devices = cast(list[str], d.pop("devices"))

        timezone = d.pop("timezone")

        devices_refs = cast(list[str], d.pop("devices_refs"))

        devices_details = FleetDevicesDetails.from_dict(d.pop("devices_details"))

        fleet = cls(
            id=id,
            ref=ref,
            name=name,
            devices=devices,
            timezone=timezone,
            devices_refs=devices_refs,
            devices_details=devices_details,
        )

        fleet.additional_properties = d
        return fleet

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
