from typing import Literal, cast

TsSeriesRetrieveUnits = Literal["$/day", "kW", "kWh/day", "W"]

TS_SERIES_RETRIEVE_UNITS_VALUES: set[TsSeriesRetrieveUnits] = {
    "$/day",
    "kW",
    "kWh/day",
    "W",
}


def check_ts_series_retrieve_units(value: str) -> TsSeriesRetrieveUnits:
    if value in TS_SERIES_RETRIEVE_UNITS_VALUES:
        return cast(TsSeriesRetrieveUnits, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_SERIES_RETRIEVE_UNITS_VALUES!r}")
