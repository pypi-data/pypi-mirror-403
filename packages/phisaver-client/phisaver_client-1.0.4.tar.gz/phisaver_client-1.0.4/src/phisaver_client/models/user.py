from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from .. import types
from ..types import UNSET, Unset

T = TypeVar("T", bound="User")


@_attrs_define
class User:
    """
    Attributes:
        devices (list[str]):
        id (int):
        email (str):
        full_name (str | Unset):
        short_name (str | Unset):
        phone (None | str | Unset):
        password (str | Unset):
    """

    devices: list[str]
    id: int
    email: str
    full_name: str | Unset = UNSET
    short_name: str | Unset = UNSET
    phone: None | str | Unset = UNSET
    password: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        devices = self.devices

        id = self.id

        email = self.email

        full_name = self.full_name

        short_name = self.short_name

        phone: None | str | Unset
        if isinstance(self.phone, Unset):
            phone = UNSET
        else:
            phone = self.phone

        password = self.password

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "devices": devices,
                "id": id,
                "email": email,
            }
        )
        if full_name is not UNSET:
            field_dict["full_name"] = full_name
        if short_name is not UNSET:
            field_dict["short_name"] = short_name
        if phone is not UNSET:
            field_dict["phone"] = phone
        if password is not UNSET:
            field_dict["password"] = password

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        for devices_item_element in self.devices:
            files.append(("devices", (None, str(devices_item_element).encode(), "text/plain")))

        files.append(("id", (None, str(self.id).encode(), "text/plain")))

        files.append(("email", (None, str(self.email).encode(), "text/plain")))

        if not isinstance(self.full_name, Unset):
            files.append(("full_name", (None, str(self.full_name).encode(), "text/plain")))

        if not isinstance(self.short_name, Unset):
            files.append(("short_name", (None, str(self.short_name).encode(), "text/plain")))

        if not isinstance(self.phone, Unset):
            if isinstance(self.phone, str):
                files.append(("phone", (None, str(self.phone).encode(), "text/plain")))
            else:
                files.append(("phone", (None, str(self.phone).encode(), "text/plain")))

        if not isinstance(self.password, Unset):
            files.append(("password", (None, str(self.password).encode(), "text/plain")))

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        devices = cast(list[str], d.pop("devices"))

        id = d.pop("id")

        email = d.pop("email")

        full_name = d.pop("full_name", UNSET)

        short_name = d.pop("short_name", UNSET)

        def _parse_phone(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        phone = _parse_phone(d.pop("phone", UNSET))

        password = d.pop("password", UNSET)

        user = cls(
            devices=devices,
            id=id,
            email=email,
            full_name=full_name,
            short_name=short_name,
            phone=phone,
            password=password,
        )

        user.additional_properties = d
        return user

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
