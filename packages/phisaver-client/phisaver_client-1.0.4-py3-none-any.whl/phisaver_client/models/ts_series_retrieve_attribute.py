from typing import Literal, cast

TsSeriesRetrieveAttribute = Literal["current", "pf", "power", "soc", "status", "voltage"]

TS_SERIES_RETRIEVE_ATTRIBUTE_VALUES: set[TsSeriesRetrieveAttribute] = {
    "current",
    "pf",
    "power",
    "soc",
    "status",
    "voltage",
}


def check_ts_series_retrieve_attribute(value: str) -> TsSeriesRetrieveAttribute:
    if value in TS_SERIES_RETRIEVE_ATTRIBUTE_VALUES:
        return cast(TsSeriesRetrieveAttribute, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_SERIES_RETRIEVE_ATTRIBUTE_VALUES!r}")
