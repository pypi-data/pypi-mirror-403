from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="Rates")


@_attrs_define
class Rates:
    """
    Attributes:
        id (int):
        import_rate (float):
        export_rate (float):
        service_rate (float):
        billing_days (int):
    """

    id: int
    import_rate: float
    export_rate: float
    service_rate: float
    billing_days: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        import_rate = self.import_rate

        export_rate = self.export_rate

        service_rate = self.service_rate

        billing_days = self.billing_days

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "import_rate": import_rate,
                "export_rate": export_rate,
                "service_rate": service_rate,
                "billing_days": billing_days,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        import_rate = d.pop("import_rate")

        export_rate = d.pop("export_rate")

        service_rate = d.pop("service_rate")

        billing_days = d.pop("billing_days")

        rates = cls(
            id=id,
            import_rate=import_rate,
            export_rate=export_rate,
            service_rate=service_rate,
            billing_days=billing_days,
        )

        rates.additional_properties = d
        return rates

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
