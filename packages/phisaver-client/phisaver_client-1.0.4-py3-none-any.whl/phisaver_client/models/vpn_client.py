from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from .. import types

T = TypeVar("T", bound="VPNClient")


@_attrs_define
class VPNClient:
    """
    Attributes:
        hostname (str):
        ip (str):
        ports (list[int]): Ping the VPNClient's IP for ports 80, 81, 82 and update the VPNClient's ports list
            Pass _refresh=True to force a refresh of the cached ports list
    """

    hostname: str
    ip: str
    ports: list[int]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        hostname = self.hostname

        ip = self.ip

        ports = self.ports

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "hostname": hostname,
                "ip": ip,
                "ports": ports,
            }
        )

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(("hostname", (None, str(self.hostname).encode(), "text/plain")))

        files.append(("ip", (None, str(self.ip).encode(), "text/plain")))

        for ports_item_element in self.ports:
            files.append(("ports", (None, str(ports_item_element).encode(), "text/plain")))

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        hostname = d.pop("hostname")

        ip = d.pop("ip")

        ports = cast(list[int], d.pop("ports"))

        vpn_client = cls(
            hostname=hostname,
            ip=ip,
            ports=ports,
        )

        vpn_client.additional_properties = d
        return vpn_client

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
