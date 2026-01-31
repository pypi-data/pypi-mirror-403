from typing import Literal, cast

TsTableRetrieveAttribute = Literal["current", "pf", "power", "soc", "status", "voltage"]

TS_TABLE_RETRIEVE_ATTRIBUTE_VALUES: set[TsTableRetrieveAttribute] = {
    "current",
    "pf",
    "power",
    "soc",
    "status",
    "voltage",
}


def check_ts_table_retrieve_attribute(value: str) -> TsTableRetrieveAttribute:
    if value in TS_TABLE_RETRIEVE_ATTRIBUTE_VALUES:
        return cast(TsTableRetrieveAttribute, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_TABLE_RETRIEVE_ATTRIBUTE_VALUES!r}")
