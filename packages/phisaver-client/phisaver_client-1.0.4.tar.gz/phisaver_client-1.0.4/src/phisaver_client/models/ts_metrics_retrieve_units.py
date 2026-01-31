from typing import Literal, cast

TsMetricsRetrieveUnits = Literal["$/day", "kW", "kWh/day", "W"]

TS_METRICS_RETRIEVE_UNITS_VALUES: set[TsMetricsRetrieveUnits] = {
    "$/day",
    "kW",
    "kWh/day",
    "W",
}


def check_ts_metrics_retrieve_units(value: str) -> TsMetricsRetrieveUnits:
    if value in TS_METRICS_RETRIEVE_UNITS_VALUES:
        return cast(TsMetricsRetrieveUnits, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_METRICS_RETRIEVE_UNITS_VALUES!r}")
