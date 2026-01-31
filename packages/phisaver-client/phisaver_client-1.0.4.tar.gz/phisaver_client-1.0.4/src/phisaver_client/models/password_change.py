from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from .. import types

T = TypeVar("T", bound="PasswordChange")


@_attrs_define
class PasswordChange:
    """
    Attributes:
        new_password1 (str):
        new_password2 (str):
    """

    new_password1: str
    new_password2: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        new_password1 = self.new_password1

        new_password2 = self.new_password2

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "new_password1": new_password1,
                "new_password2": new_password2,
            }
        )

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(("new_password1", (None, str(self.new_password1).encode(), "text/plain")))

        files.append(("new_password2", (None, str(self.new_password2).encode(), "text/plain")))

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        new_password1 = d.pop("new_password1")

        new_password2 = d.pop("new_password2")

        password_change = cls(
            new_password1=new_password1,
            new_password2=new_password2,
        )

        password_change.additional_properties = d
        return password_change

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
