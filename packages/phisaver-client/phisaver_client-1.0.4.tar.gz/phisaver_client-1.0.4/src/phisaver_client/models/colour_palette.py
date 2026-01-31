from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ColourPalette")


@_attrs_define
class ColourPalette:
    """
    Attributes:
        primary (str | Unset):
        secondary (str | Unset):
        success (str | Unset):
        warning (str | Unset):
        danger (str | Unset):
        info (str | Unset):
    """

    primary: str | Unset = UNSET
    secondary: str | Unset = UNSET
    success: str | Unset = UNSET
    warning: str | Unset = UNSET
    danger: str | Unset = UNSET
    info: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        primary = self.primary

        secondary = self.secondary

        success = self.success

        warning = self.warning

        danger = self.danger

        info = self.info

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if primary is not UNSET:
            field_dict["primary"] = primary
        if secondary is not UNSET:
            field_dict["secondary"] = secondary
        if success is not UNSET:
            field_dict["success"] = success
        if warning is not UNSET:
            field_dict["warning"] = warning
        if danger is not UNSET:
            field_dict["danger"] = danger
        if info is not UNSET:
            field_dict["info"] = info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        primary = d.pop("primary", UNSET)

        secondary = d.pop("secondary", UNSET)

        success = d.pop("success", UNSET)

        warning = d.pop("warning", UNSET)

        danger = d.pop("danger", UNSET)

        info = d.pop("info", UNSET)

        colour_palette = cls(
            primary=primary,
            secondary=secondary,
            success=success,
            warning=warning,
            danger=danger,
            info=info,
        )

        colour_palette.additional_properties = d
        return colour_palette

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
