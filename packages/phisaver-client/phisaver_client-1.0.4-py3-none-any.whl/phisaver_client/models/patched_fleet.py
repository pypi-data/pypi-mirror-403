from __future__ import annotations

import json
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from .. import types
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.patched_fleet_devices_details import PatchedFleetDevicesDetails


T = TypeVar("T", bound="PatchedFleet")


@_attrs_define
class PatchedFleet:
    """
    Attributes:
        id (int | Unset):
        ref (str | Unset):
        name (str | Unset):
        devices (list[str] | Unset):
        timezone (str | Unset):
        devices_refs (list[str] | Unset): Return a list of device refs
        devices_details (PatchedFleetDevicesDetails | Unset): Return a list of device names, id, etc.
    """

    id: int | Unset = UNSET
    ref: str | Unset = UNSET
    name: str | Unset = UNSET
    devices: list[str] | Unset = UNSET
    timezone: str | Unset = UNSET
    devices_refs: list[str] | Unset = UNSET
    devices_details: PatchedFleetDevicesDetails | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        ref = self.ref

        name = self.name

        devices: list[str] | Unset = UNSET
        if not isinstance(self.devices, Unset):
            devices = self.devices

        timezone = self.timezone

        devices_refs: list[str] | Unset = UNSET
        if not isinstance(self.devices_refs, Unset):
            devices_refs = self.devices_refs

        devices_details: dict[str, Any] | Unset = UNSET
        if not isinstance(self.devices_details, Unset):
            devices_details = self.devices_details.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if ref is not UNSET:
            field_dict["ref"] = ref
        if name is not UNSET:
            field_dict["name"] = name
        if devices is not UNSET:
            field_dict["devices"] = devices
        if timezone is not UNSET:
            field_dict["timezone"] = timezone
        if devices_refs is not UNSET:
            field_dict["devices_refs"] = devices_refs
        if devices_details is not UNSET:
            field_dict["devices_details"] = devices_details

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        if not isinstance(self.id, Unset):
            files.append(("id", (None, str(self.id).encode(), "text/plain")))

        if not isinstance(self.ref, Unset):
            files.append(("ref", (None, str(self.ref).encode(), "text/plain")))

        if not isinstance(self.name, Unset):
            files.append(("name", (None, str(self.name).encode(), "text/plain")))

        if not isinstance(self.devices, Unset):
            for devices_item_element in self.devices:
                files.append(("devices", (None, str(devices_item_element).encode(), "text/plain")))

        if not isinstance(self.timezone, Unset):
            files.append(("timezone", (None, str(self.timezone).encode(), "text/plain")))

        if not isinstance(self.devices_refs, Unset):
            for devices_refs_item_element in self.devices_refs:
                files.append(("devices_refs", (None, str(devices_refs_item_element).encode(), "text/plain")))

        if not isinstance(self.devices_details, Unset):
            files.append(
                ("devices_details", (None, json.dumps(self.devices_details.to_dict()).encode(), "application/json"))
            )

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.patched_fleet_devices_details import PatchedFleetDevicesDetails

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        ref = d.pop("ref", UNSET)

        name = d.pop("name", UNSET)

        devices = cast(list[str], d.pop("devices", UNSET))

        timezone = d.pop("timezone", UNSET)

        devices_refs = cast(list[str], d.pop("devices_refs", UNSET))

        _devices_details = d.pop("devices_details", UNSET)
        devices_details: PatchedFleetDevicesDetails | Unset
        if isinstance(_devices_details, Unset):
            devices_details = UNSET
        else:
            devices_details = PatchedFleetDevicesDetails.from_dict(_devices_details)

        patched_fleet = cls(
            id=id,
            ref=ref,
            name=name,
            devices=devices,
            timezone=timezone,
            devices_refs=devices_refs,
            devices_details=devices_details,
        )

        patched_fleet.additional_properties = d
        return patched_fleet

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
