from typing import Literal, cast

TsTableRetrieveUnits = Literal["$/day", "kW", "kWh/day", "W"]

TS_TABLE_RETRIEVE_UNITS_VALUES: set[TsTableRetrieveUnits] = {
    "$/day",
    "kW",
    "kWh/day",
    "W",
}


def check_ts_table_retrieve_units(value: str) -> TsTableRetrieveUnits:
    if value in TS_TABLE_RETRIEVE_UNITS_VALUES:
        return cast(TsTableRetrieveUnits, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_TABLE_RETRIEVE_UNITS_VALUES!r}")
